from datetime import date

from finextract.export.infrastructure.csv_exporter import CsvExporter
from finextract.mapping.domain.models import FinancialStatement, LineItem
from finextract.shared_kernel.value_objects import (
    Currency,
    FiscalPeriod,
    ReportingStandard,
    StatementCategory,
)


def test_csv_exporter_produces_header_and_row() -> None:
    statement = FinancialStatement(
        company_name="Acme Corp",
        fiscal_period=FiscalPeriod(
            fiscal_year=2023,
            start_date=date(2023, 1, 1),
            end_date=date(2023, 12, 31),
            period_label="FY2023",
        ),
        currency=Currency.USD,
        accounting_standard=ReportingStandard.US_GAAP,
        line_items=[
            LineItem(
                field_name="revenue",
                category=StatementCategory.INCOME_STATEMENT,
                value=1000.0,
                original_label="us-gaap:Revenues",
            ),
        ],
    )

    csv_bytes = CsvExporter().export(statement)
    csv_text = csv_bytes.decode("utf-8")

    assert "company_name" in csv_text
    assert "Acme Corp" in csv_text
    assert "revenue" in csv_text
