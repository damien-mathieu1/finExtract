from __future__ import annotations

from dataclasses import dataclass, field

import httpx

from finextract.extraction.domain.models import CompanySummary, FilingSummary, RawFiling
from finextract.extraction.infrastructure.xbrl_parsing import parse_xbrl_facts
from finextract.shared_kernel.errors import SourceNotFoundError

# SEC EDGAR forms known to carry XBRL financial data.
XBRL_FORM_TYPES = {"10-K", "10-Q", "10-K/A", "10-Q/A", "20-F", "40-F"}


@dataclass(slots=True)
class SecEdgarClient:
    """FilingDirectoryPort + FilingSourcePort implementation over the free,
    public SEC EDGAR APIs (no auth). SEC requires every request carry an
    identifying User-Agent ("AppName contact@email"); requests without one
    get rejected. Configure via SEC_EDGAR_USER_AGENT.

    - search_companies: matches against the static company_tickers.json
      (ticker/CIK/name for all SEC-registered companies), fetched once and
      cached in memory for the client's lifetime.
    - list_filings: reads a company's recent filings from the submissions
      API and builds a direct document URL for each XBRL-bearing filing.
    - fetch_raw_facts: downloads and parses the document at a given URL
      (normally one returned by list_filings).
    """

    user_agent: str
    _client: httpx.Client = field(init=False, repr=False)
    _ticker_cache: list[dict] | None = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        self._client = httpx.Client(headers={"User-Agent": self.user_agent}, timeout=15.0)

    def search_companies(self, query: str) -> list[CompanySummary]:
        entries = self._load_ticker_directory()
        needle = query.strip().lower()
        matches = [
            entry
            for entry in entries
            if needle in entry["title"].lower() or needle in entry["ticker"].lower()
        ]
        return [
            CompanySummary(
                cik=f"{entry['cik_str']:010d}",
                name=entry["title"],
                ticker=entry["ticker"],
            )
            for entry in matches[:25]
        ]

    def list_filings(self, cik: str) -> list[FilingSummary]:
        padded_cik = cik.zfill(10)
        response = self._client.get(f"https://data.sec.gov/submissions/CIK{padded_cik}.json")
        if response.status_code == 404:
            raise SourceNotFoundError(f"No SEC EDGAR company found for CIK '{cik}'")
        response.raise_for_status()

        recent = response.json()["filings"]["recent"]
        cik_no_leading_zeros = str(int(cik))

        filings = []
        for form, accession, filing_date, primary_document in zip(
            recent["form"],
            recent["accessionNumber"],
            recent["filingDate"],
            recent["primaryDocument"],
            strict=True,
        ):
            if form not in XBRL_FORM_TYPES:
                continue
            accession_no_dashes = accession.replace("-", "")
            document_url = (
                f"https://www.sec.gov/Archives/edgar/data/"
                f"{cik_no_leading_zeros}/{accession_no_dashes}/{primary_document}"
            )
            filings.append(
                FilingSummary(
                    accession_number=accession,
                    form_type=form,
                    filing_date=filing_date,
                    document_url=document_url,
                )
            )
        return filings

    def fetch_raw_facts(self, source_reference: str) -> RawFiling:
        response = self._client.get(source_reference)
        if response.status_code == 404:
            raise SourceNotFoundError(f"No filing document found at '{source_reference}'")
        response.raise_for_status()

        facts = parse_xbrl_facts(response.content)
        return RawFiling(
            company_identifier=source_reference,
            company_name=source_reference,
            source_url=source_reference,
            facts=facts,
        )

    def _load_ticker_directory(self) -> list[dict]:
        if self._ticker_cache is None:
            response = self._client.get("https://www.sec.gov/files/company_tickers.json")
            response.raise_for_status()
            self._ticker_cache = list(response.json().values())
        return self._ticker_cache
