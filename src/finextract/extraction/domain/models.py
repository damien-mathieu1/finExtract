from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date


@dataclass(frozen=True, slots=True)
class XbrlFact:
    """A single raw fact pulled from an XBRL/iXBRL filing, pre-mapping."""

    tag: str  # e.g. "us-gaap:Revenues"
    value: str  # raw string value, numeric parsing happens in mapping context
    context_ref: str
    unit_ref: str | None = None
    decimals: int | None = None
    scale: int | None = None  # iXBRL display multiplier: actual = value * 10**scale
    sign: str | None = None  # iXBRL negation marker: "-" means displayed value is negated
    # Resolved from the filing's <xbrli:context id=context_ref> definition.
    # Instant periods (balance-sheet facts) are represented as start == end.
    # None when the context couldn't be found/parsed.
    period_start: date | None = None
    period_end: date | None = None


@dataclass(frozen=True, slots=True)
class RawFiling:
    """The raw output of the extraction context: an identified filing and its facts."""

    company_identifier: str  # ticker or CIK
    company_name: str
    source_url: str
    facts: list[XbrlFact] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class CompanySummary:
    """A company found via a filing directory search (SEC EDGAR, EDINET,
    etc). `identifier` is whatever id that source's list_filings expects
    back (SEC: zero-padded 10-digit CIK; EDINET: E-code; ...). `source` is
    the short registry key (e.g. "sec-edgar", "edinet") the caller must pass
    back to disambiguate which adapter to use for the follow-up calls."""

    identifier: str
    name: str
    source: str
    ticker: str | None = None


@dataclass(frozen=True, slots=True)
class FilingSummary:
    """One filing belonging to a company, as returned by a filing directory
    lookup. `document_url` points directly at the XBRL/iXBRL document and is
    what a client passes to fetch_raw_facts to process this specific filing."""

    accession_number: str
    form_type: str  # "10-K", "10-Q", ...
    filing_date: str  # ISO date string
    document_url: str
