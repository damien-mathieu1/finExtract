from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import StrEnum


class Currency(StrEnum):
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    JPY = "JPY"


class ReportingStandard(StrEnum):
    IFRS = "IFRS"
    US_GAAP = "US_GAAP"
    JAPANESE_GAAP = "JAPANESE_GAAP"
    OTHER = "OTHER"


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
