from __future__ import annotations

from typing import Protocol

from finextract.mapping.domain.models import FinancialStatement


class ExportPort(Protocol):
    """Driven port: persist/serialize a FinancialStatement (Load stage)."""

    def export(self, statement: FinancialStatement) -> bytes:
        ...
