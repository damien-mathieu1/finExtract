import io
from datetime import date

import openpyxl

from finextract.export.infrastructure.pivot_exporter import (
    PivotExcelExporter,
    build_canonical_pivot,
)
from finextract.mapping.domain.models import FinancialStatement, LineItem
from finextract.shared_kernel.value_objects import (
    Currency,
    FiscalPeriod,
    ReportingStandard,
    StatementCategory,
)


def _statement(fiscal_year: int, **field_values: float) -> FinancialStatement:
    return FinancialStatement(
        company_name="Acme Corp",
        fiscal_period=FiscalPeriod(
            fiscal_year=fiscal_year,
            start_date=date(fiscal_year, 1, 1),
            end_date=date(fiscal_year, 12, 31),
            period_label=f"FY{fiscal_year}",
        ),
        currency=Currency.USD,
        accounting_standard=ReportingStandard.US_GAAP,
        line_items=[
            LineItem(
                field_name=field_name,
                category=StatementCategory.INCOME_STATEMENT,
                value=value,
                original_label=f"us-gaap:{field_name}",
            )
            for field_name, value in field_values.items()
        ],
    )


def test_build_canonical_pivot_keeps_template_order_and_blanks_missing_rows() -> None:
    statements = [_statement(2023, revenue=1000.0)]

    df = build_canonical_pivot(statements, StatementCategory.INCOME_STATEMENT)

    assert list(df["field_name"])[0] == "revenue"
    revenue_row = df[df["field_name"] == "revenue"].iloc[0]
    assert revenue_row["FY2023"] == 1000.0
    gross_profit_row = df[df["field_name"] == "gross_profit"].iloc[0]
    assert gross_profit_row["FY2023"] is None or gross_profit_row.isna()["FY2023"]


def test_build_canonical_pivot_appends_unmatched_fields() -> None:
    statements = [_statement(2023, revenue=1000.0, some_unmapped_field=42.0)]

    df = build_canonical_pivot(statements, StatementCategory.INCOME_STATEMENT)

    extra = df[df["field_name"] == "some_unmapped_field"]
    assert len(extra) == 1
    assert extra.iloc[0]["bloomberg_code"] == ""
    assert extra.iloc[0]["FY2023"] == 42.0


def test_build_canonical_pivot_multi_year_columns_chronological() -> None:
    statements = [_statement(2022, revenue=900.0), _statement(2021, revenue=800.0)]

    df = build_canonical_pivot(statements, StatementCategory.INCOME_STATEMENT)

    period_cols = [c for c in df.columns if c.startswith("FY")]
    assert period_cols == ["FY2021", "FY2022"]


def test_pivot_excel_exporter_writes_three_sheets() -> None:
    statements = [_statement(2023, revenue=1000.0)]

    payload = PivotExcelExporter().export(statements)
    workbook = openpyxl.load_workbook(io.BytesIO(payload))

    assert workbook.sheetnames == ["PL", "BS", "CS"]
