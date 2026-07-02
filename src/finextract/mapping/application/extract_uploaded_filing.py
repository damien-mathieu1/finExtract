from __future__ import annotations

from dataclasses import dataclass

from finextract.extraction.domain.models import RawFiling
from finextract.extraction.infrastructure.xbrl_parsing import parse_xbrl_facts
from finextract.mapping.domain.models import FinancialStatement
from finextract.mapping.domain.ports import TaxonomyMapperPort


@dataclass(slots=True)
class ExtractUploadedFiling:
    """Use case: parse+normalize an XBRL/iXBRL file uploaded directly by a
    user, bypassing FilingSourcePort (no local-fixture-directory lookup or
    SEC EDGAR fetch involved) since the bytes are already in hand."""

    mapper: TaxonomyMapperPort

    def __call__(self, filename: str, content: bytes) -> FinancialStatement:
        facts = parse_xbrl_facts(content)
        raw_filing = RawFiling(
            company_identifier=filename,
            company_name=filename,
            source_url=f"upload:{filename}",
            facts=facts,
        )
        return self.mapper.normalize(raw_filing)
