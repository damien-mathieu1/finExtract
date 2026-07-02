from __future__ import annotations

import io

import pandas as pd

from finextract.export.infrastructure.csv_exporter import statement_to_dataframe
from finextract.mapping.domain.models import FinancialStatement


class ExcelExporter:
    """ExportPort implementation writing a FinancialStatement as an XLSX workbook."""

    def export(self, statement: FinancialStatement) -> bytes:
        df = statement_to_dataframe(statement)
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="FinancialStatement")
        return buffer.getvalue()
