from __future__ import annotations

from dataclasses import dataclass

from finextract.extraction.domain.models import RawFiling
from finextract.extraction.domain.ports import FilingSourcePort


@dataclass(slots=True)
class ExtractFiling:
    """Use case: retrieve the raw facts for a company's filing via whichever
    FilingSourcePort adapter is injected (XBRL now, PDF/OCR later)."""

    source: FilingSourcePort

    def __call__(self, company_identifier: str) -> RawFiling:
        return self.source.fetch_raw_facts(company_identifier)
