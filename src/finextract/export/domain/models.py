from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class ExtractionSummary:
    """A lightweight record of one persisted extraction, without its full
    line item detail (use ExtractionQueryPort.get_extraction for that)."""

    id: int
    company_name: str
    fiscal_year: int
    period_label: str
    currency: str
    accounting_standard: str
    source_reference: str
    extracted_at: datetime
