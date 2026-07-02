from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from finextract.extraction.domain.models import RawFiling
from finextract.extraction.infrastructure.xbrl_parsing import parse_xbrl_facts
from finextract.shared_kernel.errors import SourceNotFoundError


@dataclass(slots=True)
class LocalXbrlFileAdapter:
    """FilingSourcePort implementation reading XBRL/iXBRL files from a local
    directory, keyed by company_identifier -> "<identifier>.xbrl".

    Used for local dev/testing with fixture filings. For real SEC filings,
    see SecEdgarFilingSource, which implements the same port over HTTP.
    """

    filings_dir: Path

    def fetch_raw_facts(self, company_identifier: str) -> RawFiling:
        filing_path = self.filings_dir / f"{company_identifier}.xbrl"
        if not filing_path.exists():
            raise SourceNotFoundError(
                f"No local XBRL filing found for '{company_identifier}' at {filing_path}"
            )

        facts = parse_xbrl_facts(filing_path.read_bytes())

        return RawFiling(
            company_identifier=company_identifier,
            company_name=company_identifier,
            source_url=str(filing_path),
            facts=facts,
        )
