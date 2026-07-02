from __future__ import annotations

from dataclasses import dataclass

from finextract.extraction.domain.ports import FilingSourcePort
from finextract.mapping.domain.models import FinancialStatement
from finextract.mapping.domain.ports import TaxonomyMapperPort


@dataclass(slots=True)
class NormalizeStatement:
    """Use case: extract a filing then map it to the standard schema.

    Orchestrates across the extraction and mapping bounded contexts via their
    ports only — never touches either context's infrastructure directly.
    """

    source: FilingSourcePort
    mapper: TaxonomyMapperPort

    def __call__(self, company_identifier: str) -> FinancialStatement:
        raw_filing = self.source.fetch_raw_facts(company_identifier)
        return self.mapper.normalize(raw_filing)
