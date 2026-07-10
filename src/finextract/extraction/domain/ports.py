from __future__ import annotations

from typing import Protocol

from finextract.extraction.domain.models import CompanySummary, FilingSummary, RawFiling


class FilingSourcePort(Protocol):
    """Driven port: fetch+parse a filing into raw facts.

    Implemented today by a local-file adapter (dev/testing) and a SEC EDGAR
    adapter (real filings, by document URL). A future PDF/OCR adapter
    implements the same port, so extraction/application and everything
    downstream (mapping, export) needs no changes to gain a fallback source.
    """

    def fetch_raw_facts(self, source_reference: str) -> RawFiling: ...


class FilingDirectoryPort(Protocol):
    """Driven port: browse a filing source to find what's available before
    fetching anything. Powers the "search company -> pick a filing" flow;
    fetching/parsing the chosen filing is a separate step via FilingSourcePort.
    """

    def search_companies(self, query: str) -> list[CompanySummary]: ...

    def list_filings(self, identifier: str) -> list[FilingSummary]: ...
