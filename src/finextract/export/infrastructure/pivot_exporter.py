from __future__ import annotations

import io

import pandas as pd

from finextract.export.infrastructure.statement_template import load_statement_template
from finextract.mapping.domain.models import FinancialStatement
from finextract.shared_kernel.value_objects import StatementCategory


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


class PivotExcelExporter:
    """PivotExportPort implementation writing several statements as a
    Bloomberg-style XLSX workbook: one sheet per statement (PL/BS/CS), rows
    in canonical template order (bloomberg_code, label, field_name), columns
    = period_label."""

    def export(self, statements: list[FinancialStatement]) -> bytes:
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            for category, sheet_name in _SHEET_NAMES.items():
                df = build_canonical_pivot(statements, category)
                df.to_excel(writer, index=False, sheet_name=sheet_name)
        return buffer.getvalue()
