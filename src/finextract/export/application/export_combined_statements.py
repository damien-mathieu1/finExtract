from __future__ import annotations

from dataclasses import dataclass

from finextract.export.domain.ports import PivotExportPort
from finextract.mapping.domain.models import FinancialStatement


@dataclass(slots=True)
class ExportCombinedStatements:
    """Use case: hand several normalized FinancialStatements (e.g. multiple
    fiscal years selected by a user) to a PivotExportPort adapter that
    combines them into one pivoted export."""

    exporter: PivotExportPort

    def __call__(self, statements: list[FinancialStatement]) -> bytes:
        return self.exporter.export(statements)
