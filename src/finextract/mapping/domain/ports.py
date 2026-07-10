from __future__ import annotations

from typing import Protocol

from finextract.extraction.domain.models import RawFiling
from finextract.mapping.domain.models import FinancialStatement


class TaxonomyMapperPort(Protocol):
    """Driven port: normalize a RawFiling's facts into the standard schema.

    Returns one FinancialStatement per distinct resolved reporting period
    found in the filing (real filings report several comparative years/
    periods side by side)."""

    def normalize(self, raw_filing: RawFiling) -> list[FinancialStatement]: ...
