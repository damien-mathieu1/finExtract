from __future__ import annotations

from dataclasses import dataclass

from finextract.export.domain.ports import ExtractionPersisterPort
from finextract.mapping.application.normalize_statement import NormalizeStatement
from finextract.mapping.domain.models import FinancialStatement


@dataclass(slots=True)
class PersistAndNormalizeStatement:
    """Decorates a NormalizeStatement use case: runs it, then persists the
    result as a side effect via an ExtractionPersisterPort, independent of
    whatever export format the caller also requested."""

    inner: NormalizeStatement
    persister: ExtractionPersisterPort

    def __call__(self, source_reference: str) -> FinancialStatement:
        statement = self.inner(source_reference)
        self.persister.persist(statement, source_reference)
        return statement
