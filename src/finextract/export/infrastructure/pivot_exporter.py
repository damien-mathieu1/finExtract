from __future__ import annotations

import io
from dataclasses import dataclass
from typing import Literal

import pandas as pd
from openpyxl import Workbook
from openpyxl.chart import AreaChart, BarChart, LineChart, Reference
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.worksheet import Worksheet

from finextract.export.infrastructure.statement_template import load_statement_template
from finextract.mapping.domain.models import FinancialStatement
from finextract.shared_kernel.value_objects import StatementCategory

ChartType = Literal["bar", "line", "area"]


@dataclass(frozen=True, slots=True)
class FigureSpec:
    """Which metrics to plot on the workbook's extra "Figure" sheet, and as
    what native Excel chart type - mirrors the metric/chart-type selection
    made on the frontend Charts page."""

    metrics: tuple[tuple[str, StatementCategory], ...]
    chart_type: ChartType = "bar"
    title: str = "Figure"


def build_pivot_dataframe(statements: list[FinancialStatement]) -> pd.DataFrame:
    """Builds a wide table: one row per (category, field_name), one column
    per distinct period_label found across the given statements, sorted by
    fiscal_year. Statements are expected to belong to the same company but
    this isn't enforced - callers (the combine endpoint) decide what's a
    sensible selection."""
    ordered_labels = [
        s.fiscal_period.period_label
        for s in sorted(statements, key=lambda s: s.fiscal_period.fiscal_year)
    ]

    long_rows = [
        {
            "category": li.category.value,
            "field_name": li.field_name,
            "period_label": statement.fiscal_period.period_label,
            "value": li.value,
        }
        for statement in statements
        for li in statement.line_items
    ]
    if not long_rows:
        return pd.DataFrame(columns=["category", "field_name", *ordered_labels])

    long_df = pd.DataFrame(long_rows)
    pivoted = long_df.pivot_table(
        index=["category", "field_name"],
        columns="period_label",
        values="value",
        aggfunc="first",
    )
    # Reorder/limit columns to the periods actually present, chronologically.
    pivoted = pivoted.reindex(
        columns=[label for label in ordered_labels if label in pivoted.columns]
    )
    return pivoted.reset_index()


def build_canonical_pivot(
    statements: list[FinancialStatement], category: StatementCategory
) -> pd.DataFrame:
    """Wide table for one statement category, rows in the fixed canonical
    template order (bloomberg_code, label, field_name), one column per
    fiscal-year period_label. Template rows with no matching data render
    blank rather than being omitted. Real field_names present in the data
    but not covered by the template are appended at the end (code/label
    blank) so nothing is silently dropped."""
    template_rows = [r for r in load_statement_template() if r.category == category]

    pivoted = build_pivot_dataframe(statements)
    period_cols = [c for c in pivoted.columns if c not in ("category", "field_name")]
    cat_df = pivoted[pivoted["category"] == category.value].set_index("field_name")

    template_fields = {r.standard_field for r in template_rows}
    out_rows = []
    for r in template_rows:
        row = {"bloomberg_code": r.bloomberg_code, "label": r.label, "field_name": r.standard_field}
        has_data = r.standard_field in cat_df.index
        for col in period_cols:
            row[col] = cat_df.loc[r.standard_field, col] if has_data else None
        out_rows.append(row)

    for field_name in [f for f in cat_df.index if f not in template_fields]:
        row = {"bloomberg_code": "", "label": "", "field_name": field_name}
        for col in period_cols:
            row[col] = cat_df.loc[field_name, col]
        out_rows.append(row)

    return pd.DataFrame(out_rows, columns=["bloomberg_code", "label", "field_name", *period_cols])


class PivotCsvExporter:
    """PivotExportPort implementation writing several statements as one
    combined CSV: rows = category + field_name, columns = period_label."""

    def export(self, statements: list[FinancialStatement]) -> bytes:
        df = build_pivot_dataframe(statements)
        buffer = io.StringIO()
        df.to_csv(buffer, index=False)
        return buffer.getvalue().encode("utf-8")


_SHEET_NAMES: dict[StatementCategory, str] = {
    StatementCategory.INCOME_STATEMENT: "PL",
    StatementCategory.BALANCE_SHEET: "BS",
    StatementCategory.CASH_FLOW: "CS",
}
_SHEET_TITLES: dict[StatementCategory, str] = {
    StatementCategory.INCOME_STATEMENT: "Income Statement",
    StatementCategory.BALANCE_SHEET: "Balance Sheet",
    StatementCategory.CASH_FLOW: "Cash Flow Statement",
}

_ID_COLUMNS = ("bloomberg_code", "label", "field_name")
_TITLE_ROW = 1
_SUBTITLE_ROW = 2
_HEADER_ROW = 3
_DATA_START_ROW = 4

_NAVY = "1F3864"
_BLUE = "2F5597"
_LIGHT_GREY = "F2F2F2"
_BORDER_GREY = "D9D9D9"
_THIN_GREY = Side(style="thin", color=_BORDER_GREY)
_CELL_BORDER = Border(left=_THIN_GREY, right=_THIN_GREY, top=_THIN_GREY, bottom=_THIN_GREY)


def _max_formatted_length(series: pd.Series) -> int:
    """Widest rendered width a value in this column will need once displayed
    with the "#,##0;(#,##0)" thousands-separator format (negatives wrapped
    in parens add 2 chars vs the plain digit count)."""
    max_len = 0
    for value in series:
        if value is None or (isinstance(value, float) and pd.isna(value)):
            continue
        digits = f"{abs(value):,.0f}"
        max_len = max(max_len, len(digits) + (2 if value < 0 else 0))
    return max_len


def _style_statement_sheet(ws: Worksheet, df: pd.DataFrame, *, title: str, subtitle: str) -> None:
    """Applies the Bloomberg-style look (title band, colored header, boxed
    grid, zebra striping, thousands-formatted numbers) to a worksheet a
    DataFrame was already written into via to_excel(startrow=2)."""
    n_cols = len(df.columns)
    n_rows = len(df)
    last_col_letter = get_column_letter(n_cols)

    ws.merge_cells(f"A{_TITLE_ROW}:{last_col_letter}{_TITLE_ROW}")
    title_cell = ws.cell(row=_TITLE_ROW, column=1, value=title)
    title_cell.font = Font(bold=True, size=13, color="FFFFFF")
    title_cell.fill = PatternFill("solid", fgColor=_NAVY)
    title_cell.alignment = Alignment(horizontal="left", vertical="center", indent=1)
    ws.row_dimensions[_TITLE_ROW].height = 24

    ws.merge_cells(f"A{_SUBTITLE_ROW}:{last_col_letter}{_SUBTITLE_ROW}")
    subtitle_cell = ws.cell(row=_SUBTITLE_ROW, column=1, value=subtitle)
    subtitle_cell.font = Font(italic=True, size=9, color="595959")
    subtitle_cell.alignment = Alignment(horizontal="left", vertical="center", indent=1)
    ws.row_dimensions[_SUBTITLE_ROW].height = 16

    period_columns = [c for c in df.columns if c not in _ID_COLUMNS]
    for col_idx, col_name in enumerate(df.columns, start=1):
        header_cell = ws.cell(row=_HEADER_ROW, column=col_idx)
        header_cell.font = Font(bold=True, size=10, color="FFFFFF")
        header_cell.fill = PatternFill("solid", fgColor=_BLUE)
        header_cell.alignment = Alignment(
            horizontal="center" if col_name in period_columns else "left",
            vertical="center",
        )
        header_cell.border = _CELL_BORDER
        if col_name in period_columns:
            width = max(12, _max_formatted_length(df[col_name]) + 2)
        else:
            width = {"bloomberg_code": 20, "label": 34}.get(col_name, 26)
        ws.column_dimensions[get_column_letter(col_idx)].width = width
    ws.row_dimensions[_HEADER_ROW].height = 18

    for row_offset in range(n_rows):
        row_idx = _DATA_START_ROW + row_offset
        is_striped = row_offset % 2 == 1
        for col_idx, col_name in enumerate(df.columns, start=1):
            cell = ws.cell(row=row_idx, column=col_idx)
            cell.border = _CELL_BORDER
            if is_striped:
                cell.fill = PatternFill("solid", fgColor=_LIGHT_GREY)
            if col_name == "label":
                cell.font = Font(bold=True, size=10)
            elif col_name == "bloomberg_code":
                cell.font = Font(size=8, color="808080")
            elif col_name == "field_name":
                cell.font = Font(size=8, italic=True, color="808080")
            elif col_name in period_columns:
                cell.number_format = "#,##0;(#,##0)"
                cell.alignment = Alignment(horizontal="right")

    ws.freeze_panes = f"D{_DATA_START_ROW}"


def _figure_sheet_labels() -> dict[tuple[StatementCategory, str], str]:
    return {(row.category, row.standard_field): row.label for row in load_statement_template()}


def _write_figure_sheet(
    wb: Workbook, statements: list[FinancialStatement], figure: FigureSpec
) -> None:
    """Adds a "Figure" sheet: a small period x metric data table plus a
    native Excel chart object bound to it, mirroring the metric selection
    and chart type chosen on the frontend Charts page. Native chart (not an
    embedded image) so it stays editable/re-themeable in Excel."""
    labels = _figure_sheet_labels()
    ordered_statements = sorted(statements, key=lambda s: s.fiscal_period.fiscal_year)
    periods = list(dict.fromkeys(s.fiscal_period.period_label for s in ordered_statements))

    ws = wb.create_sheet("Figure")
    header = ["Period"] + [
        labels.get((category, field_name), field_name) for field_name, category in figure.metrics
    ]
    ws.append(header)
    for cell in ws[1]:
        cell.font = Font(bold=True, size=10, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor=_BLUE)

    for period in periods:
        row = [period]
        for field_name, category in figure.metrics:
            value = None
            for statement in ordered_statements:
                if statement.fiscal_period.period_label != period:
                    continue
                for li in statement.line_items:
                    if li.field_name == field_name and li.category == category:
                        value = li.value
                        break
            row.append(value)
        ws.append(row)

    ws.column_dimensions["A"].width = 16
    for col_idx in range(2, len(header) + 1):
        ws.column_dimensions[get_column_letter(col_idx)].width = 16
        for row_idx in range(2, len(periods) + 2):
            ws.cell(row=row_idx, column=col_idx).number_format = "#,##0;(#,##0)"

    n_rows = len(periods) + 1
    n_cols = len(header)
    chart_cls = {"bar": BarChart, "line": LineChart, "area": AreaChart}[figure.chart_type]
    chart = chart_cls()
    if isinstance(chart, BarChart):
        chart.type = "col"
    chart.title = figure.title
    chart.y_axis.title = "Value"
    chart.x_axis.title = "Period"
    chart.width = 24
    chart.height = 12

    data = Reference(ws, min_col=2, max_col=n_cols, min_row=1, max_row=n_rows)
    categories = Reference(ws, min_col=1, min_row=2, max_row=n_rows)
    chart.add_data(data, titles_from_data=True)
    chart.set_categories(categories)
    ws.add_chart(chart, f"A{n_rows + 3}")


class PivotExcelExporter:
    """PivotExportPort implementation writing several statements as a
    Bloomberg-style XLSX workbook: one sheet per statement (PL/BS/CS), rows
    in canonical template order (bloomberg_code, label, field_name), columns
    = period_label. Optionally appends a "Figure" sheet (data table + native
    chart) when a FigureSpec is given."""

    def export(
        self, statements: list[FinancialStatement], figure: FigureSpec | None = None
    ) -> bytes:
        company_name = statements[0].company_name if statements else ""
        standards = {s.accounting_standard.value.replace("_", " ") for s in statements}
        currencies = {s.currency.value for s in statements}
        subtitle = f"{' / '.join(sorted(standards))} · {' / '.join(sorted(currencies))}"

        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            for category, sheet_name in _SHEET_NAMES.items():
                df = build_canonical_pivot(statements, category)
                df.to_excel(writer, index=False, sheet_name=sheet_name, startrow=_HEADER_ROW - 1)
                ws = writer.sheets[sheet_name]
                _style_statement_sheet(
                    ws,
                    df,
                    title=f"{company_name} — {_SHEET_TITLES[category]}",
                    subtitle=subtitle,
                )
            if figure is not None and figure.metrics:
                _write_figure_sheet(writer.book, statements, figure)
        return buffer.getvalue()
