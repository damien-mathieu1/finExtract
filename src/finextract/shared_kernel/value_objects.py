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
    AUD = "AUD"
    BRL = "BRL"
    CAD = "CAD"
    CHF = "CHF"
    CNY = "CNY"
    DKK = "DKK"
    HKD = "HKD"
    ILS = "ILS"
    INR = "INR"
    MXN = "MXN"
    NOK = "NOK"
    SEK = "SEK"
    TWD = "TWD"
    UNKNOWN = "XXX"  # ISO 4217 "no currency": reported in a code not listed above


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
    """A reporting period, e.g. FY2023 or the 3 months to 2023-06-30."""

    fiscal_year: int
    start_date: date
    end_date: date
    period_label: str  # "FY2023", "3M to 2023-06-30", "As of 2023-12-31"

    def __post_init__(self) -> None:
        if self.start_date > self.end_date:
            raise ValueError("start_date must not be after end_date")
