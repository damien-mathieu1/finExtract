from __future__ import annotations

import io

import pandas as pd

from finextract.mapping.domain.models import FinancialStatement


class CsvExporter:
    """ExportPort implementation writing a FinancialStatement as CSV bytes."""

    def export(self, statement: FinancialStatement) -> bytes:
        df = statement_to_dataframe(statement)
        buffer = io.StringIO()
        df.to_csv(buffer, index=False)
        return buffer.getvalue().encode("utf-8")


def statement_to_dataframe(statement: FinancialStatement) -> pd.DataFrame:
    rows = [
        {
            "company_name": statement.company_name,
            "fiscal_year": statement.fiscal_period.fiscal_year,
            "period_label": statement.fiscal_period.period_label,
            "currency": statement.currency.value,
            "accounting_standard": statement.accounting_standard.value,
            "category": li.category.value,
            "field_name": li.field_name,
            "value": li.value,
            "original_label": li.original_label,
            "source": li.source,
            "page_number": li.page_number,
            "confidence_score": li.confidence_score,
        }
        for li in statement.line_items
    ]
    return pd.DataFrame(rows)
