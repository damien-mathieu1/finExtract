from __future__ import annotations

from dataclasses import dataclass

from finextract.shared_kernel.value_objects import Currency, FiscalPeriod, ReportingStandard


@dataclass(slots=True)
class LineItem:
    """One standardized financial figure, traceable back to its source tag."""

    field_name: str  # standard schema field, e.g. "revenue", "net_income"
    value: float | None
    original_label: str  # source taxonomy tag, e.g. "us-gaap:Revenues"
    source: str = "XBRL"  # "XBRL" | "PDF"
    page_number: int | None = None  # PDF extraction only
    confidence_score: float | None = None  # PDF extraction only


@dataclass(slots=True)
class FinancialStatement:
    """The standard schema output: company info + normalized line items."""

    company_name: str
    fiscal_period: FiscalPeriod
    currency: Currency
    accounting_standard: ReportingStandard
    line_items: list[LineItem]

    def get(self, field_name: str) -> LineItem | None:
        return next((li for li in self.line_items if li.field_name == field_name), None)
