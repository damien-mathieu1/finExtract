from __future__ import annotations

from dataclasses import dataclass

from finextract.export.domain.ports import ExportPort
from finextract.mapping.domain.models import FinancialStatement


@dataclass(slots=True)
class ExportStatement:
    """Use case: hand a normalized FinancialStatement to whichever
    ExportPort adapter is injected (CSV, Excel, Postgres, ...)."""

    exporter: ExportPort

    def __call__(self, statement: FinancialStatement) -> bytes:
        return self.exporter.export(statement)
