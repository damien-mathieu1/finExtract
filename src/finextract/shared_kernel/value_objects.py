from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import StrEnum


class Currency(StrEnum):
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    JPY = "JPY"
    KRW = "KRW"


class ReportingStandard(StrEnum):
    IFRS = "IFRS"
    US_GAAP = "US_GAAP"
    JAPANESE_GAAP = "JAPANESE_GAAP"
    OTHER = "OTHER"


class StatementCategory(StrEnum):
    """Which of the three standard financial statements a line item belongs
    to, for grouping in exports/UI (income statement / balance sheet / cash
    flow statement)."""

    INCOME_STATEMENT = "income_statement"
    BALANCE_SHEET = "balance_sheet"
    CASH_FLOW = "cash_flow"


@dataclass(frozen=True, slots=True)
class FiscalPeriod:
    """A reporting period, e.g. FY2023 or Q3 2023."""

    fiscal_year: int
    start_date: date
    end_date: date
    period_label: str  # "FY2023", "Q3 2023", etc.

    def __post_init__(self) -> None:
        if self.start_date > self.end_date:
            raise ValueError("start_date must not be after end_date")
