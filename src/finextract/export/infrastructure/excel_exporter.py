from __future__ import annotations

from finextract.export.infrastructure.pivot_exporter import PivotExcelExporter
from finextract.mapping.domain.models import FinancialStatement


class ExcelExporter:
    """ExportPort implementation writing a single FinancialStatement as an
    XLSX workbook, reusing the same Bloomberg-style PL/BS/CS layout as the
    combined export (one period column instead of several)."""

    def export(self, statement: FinancialStatement) -> bytes:
        return PivotExcelExporter().export([statement])
