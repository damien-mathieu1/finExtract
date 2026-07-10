from __future__ import annotations

import csv
import io
import zipfile
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import date, timedelta

import httpx

from finextract.extraction.domain.models import CompanySummary, FilingSummary, RawFiling
from finextract.extraction.infrastructure.xbrl_parsing import parse_xbrl_facts
from finextract.shared_kernel.errors import SourceNotFoundError

_CODE_LIST_URL = "https://disclosure2dl.edinet-fsa.go.jp/searchdocument/codelist/Edinetcode.zip"
_API_BASE = "https://api.edinet-fsa.go.jp/api/v2"

# EDINET document type codes carrying XBRL financial data (securities
# reports / annual, quarterly and semi-annual reports). See EDINET API spec
# "ordinanceCode"/"formCode" reference for the full list; these cover the
# filings equivalent to SEC 10-K/10-Q.
XBRL_DOC_TYPE_CODES = {"120", "130", "140", "150"}  # yuho, semi-annual, quarterly, extraordinary

# EDINET has no "list filings for this company" endpoint - documents.json is
# queried per calendar day. list_filings scans back this many days to build
# a filing history. Default window is deliberately small (most companies
# file 1-2 XBRL reports within any 4-month span); callers that want older
# history pass a larger `lookback_days` explicitly ("load more" in the UI).
_DEFAULT_LOOKBACK_DAYS = 120
_MAX_LOOKBACK_DAYS = 800

# Day-scan requests are independent and EDINET has no documented rate limit
# for this endpoint, so fetch them concurrently instead of one-at-a-time -
# sequential scanning of 400 days took ~5 minutes end to end in testing.
_DAY_SCAN_WORKERS = 20


@dataclass(slots=True)
class EdinetClient:
    """FilingDirectoryPort + FilingSourcePort implementation over EDINET
    (Japan's financial disclosure system), api.edinet-fsa.go.jp/api/v2.
    Requires a free EDINET API subscription key, configured via
    EDINET_API_KEY.

    - search_companies: matches against EDINET's daily company code list
      (EDINET code, name, ticker for every registered filer), downloaded
      once and cached in memory for the client's lifetime.
    - list_filings: EDINET's documents.json endpoint is queried by calendar
      date, not by company, so this scans the last `_LOOKBACK_DAYS` days and
      filters to the given EDINET code's XBRL-bearing filings. Slower than
      SEC's per-company submissions API, but there's no alternative EDINET
      endpoint. Days are fetched concurrently and each day's raw result is
      cached (dates are immutable once past), so the first lookup pays the
      full scan cost once and every subsequent lookup - for any company -
      is served from memory.
    - fetch_raw_facts: downloads the filing's XBRL submission ZIP and parses
      the instance document inside it (EDINET, unlike SEC, serves a ZIP
      package rather than the XBRL/iXBRL document directly).
    """

    api_key: str
    _client: httpx.Client = field(init=False, repr=False)
    _company_cache: list[dict] | None = field(default=None, init=False, repr=False)
    _day_docs_cache: dict[str, list[dict]] = field(default_factory=dict, init=False, repr=False)

    def __post_init__(self) -> None:
        self._client = httpx.Client(timeout=20.0)

    def search_companies(self, query: str) -> list[CompanySummary]:
        entries = self._load_company_directory()
        needle = query.strip().lower()
        matches = [
            entry
            for entry in entries
            if needle in entry["name"].lower()
            or needle in entry["name_en"].lower()
            or needle in (entry["ticker"] or "").lower()
        ]
        return [
            CompanySummary(
                identifier=entry["edinet_code"],
                name=entry["name_en"] or entry["name"],
                source="edinet",
                ticker=entry["ticker"] or None,
            )
            for entry in matches[:25]
        ]

    def list_filings(
        self, identifier: str, lookback_days: int | None = None
    ) -> list[FilingSummary]:
        days = min(lookback_days or _DEFAULT_LOOKBACK_DAYS, _MAX_LOOKBACK_DAYS)
        self._ensure_days_cached(days)

        # Filters over the full cache (not just this call's window) since
        # earlier/larger lookups may have already warmed days beyond it -
        # no reason to throw that data away.
        filings: list[FilingSummary] = []
        for day_iso, docs in self._day_docs_cache.items():
            for doc in docs:
                if doc.get("edinetCode") != identifier:
                    continue
                if doc.get("xbrlFlag") != "1":
                    continue
                if doc.get("docTypeCode") not in XBRL_DOC_TYPE_CODES:
                    continue
                filings.append(
                    FilingSummary(
                        accession_number=doc["docID"],
                        form_type=doc.get("docDescription") or doc["docTypeCode"],
                        filing_date=doc.get("submitDateTime", day_iso)[:10],
                        document_url=doc["docID"],
                    )
                )
        if not filings:
            raise SourceNotFoundError(f"No EDINET filings found for EDINET code '{identifier}'")
        return filings

    def _ensure_days_cached(self, lookback_days: int) -> None:
        today = date.today()
        missing_days = [
            today - timedelta(days=offset)
            for offset in range(lookback_days)
            if (today - timedelta(days=offset)).isoformat() not in self._day_docs_cache
        ]
        if not missing_days:
            return

        with ThreadPoolExecutor(max_workers=_DAY_SCAN_WORKERS) as pool:
            results = pool.map(self._fetch_day_docs, missing_days)
            for day, docs in zip(missing_days, results, strict=True):
                self._day_docs_cache[day.isoformat()] = docs

    def _fetch_day_docs(self, day: date) -> list[dict]:
        response = self._client.get(
            f"{_API_BASE}/documents.json",
            params={"date": day.isoformat(), "type": 2, "Subscription-Key": self.api_key},
        )
        if response.status_code == 404:
            return []
        response.raise_for_status()
        return response.json().get("results", []) or []

    def fetch_raw_facts(self, source_reference: str) -> RawFiling:
        response = self._client.get(
            f"{_API_BASE}/documents/{source_reference}",
            params={"type": 1, "Subscription-Key": self.api_key},
        )
        if response.status_code == 404:
            raise SourceNotFoundError(f"No EDINET document found for docID '{source_reference}'")
        response.raise_for_status()

        xbrl_bytes = _extract_instance_document(response.content)
        facts = parse_xbrl_facts(xbrl_bytes)
        return RawFiling(
            company_identifier=source_reference,
            company_name=source_reference,
            source_url=source_reference,
            facts=facts,
        )

    def _load_company_directory(self) -> list[dict]:
        if self._company_cache is None:
            response = self._client.get(_CODE_LIST_URL)
            response.raise_for_status()
            self._company_cache = _parse_code_list(response.content)
        return self._company_cache


def _extract_instance_document(zip_bytes: bytes) -> bytes:
    """EDINET's document ZIP contains the XBRL instance under
    XBRL/PublicDoc/*.xbrl. Pick the first .xbrl file found there (falls back
    to any top-level .xbrl if the expected path shape isn't present)."""
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as archive:
        candidates = [
            name for name in archive.namelist() if name.endswith(".xbrl") and "PublicDoc" in name
        ] or [name for name in archive.namelist() if name.endswith(".xbrl")]
        if not candidates:
            raise SourceNotFoundError("EDINET submission ZIP contained no XBRL instance document")
        return archive.read(candidates[0])


def _parse_code_list(zip_bytes: bytes) -> list[dict]:
    """EDINET's code list ships as a Shift-JIS CSV inside a ZIP, with 2
    header rows before the data starts. Confirmed columns (0-indexed):
    0 EDINET code, 6 filer name (Japanese), 7 filer name (English, often
    blank for non-listed filers), 11 securities code - a 5-digit code
    (4-digit ticker + trailing check digit) for listed filers, blank
    otherwise."""
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as archive:
        csv_name = next(name for name in archive.namelist() if name.endswith(".csv"))
        raw = archive.read(csv_name).decode("shift_jis", errors="replace")

    rows = list(csv.reader(io.StringIO(raw)))
    entries = []
    for row in rows[2:]:
        if len(row) < 12 or not row[0]:
            continue
        securities_code = row[11].strip()
        entries.append(
            {
                "edinet_code": row[0],
                "name": row[6],
                "name_en": row[7].strip(),
                "ticker": securities_code[:4] if securities_code else None,
            }
        )
    return entries
