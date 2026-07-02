from __future__ import annotations

from dataclasses import dataclass, field


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


@dataclass(frozen=True, slots=True)
class RawFiling:
    """The raw output of the extraction context: an identified filing and its facts."""

    company_identifier: str  # ticker or CIK
    company_name: str
    source_url: str
    facts: list[XbrlFact] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class CompanySummary:
    """A company found via a filing directory search (SEC EDGAR, etc.)."""

    cik: str  # zero-padded 10-digit, e.g. "0000320193"
    name: str
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
