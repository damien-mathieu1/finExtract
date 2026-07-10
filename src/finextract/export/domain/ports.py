from __future__ import annotations

from typing import Protocol

from finextract.export.domain.models import ExtractionSummary
from finextract.mapping.domain.models import FinancialStatement


class ExportPort(Protocol):
    """Driven port: persist/serialize a FinancialStatement (Load stage)."""

    def export(self, statement: FinancialStatement) -> bytes: ...


class ExtractionPersisterPort(Protocol):
    """Driven port: record a normalized FinancialStatement as history, keyed
    by the source_reference it was extracted from. Re-persisting the same
    source_reference upserts (replaces line items, bumps extracted_at) rather
    than accumulating duplicate history rows."""

    def persist(
        self,
        statement: FinancialStatement,
        source_reference: str,
        *,
        cik: str | None = None,
        ticker: str | None = None,
        label: str | None = None,
    ) -> None: ...


class ExtractionQueryPort(Protocol):
    """Driven port: query previously persisted extractions."""

    def list_extractions(
        self, *, company_identifier: str | None = None, source_reference: str | None = None
    ) -> list[ExtractionSummary]: ...

    def get_extraction_ids_for_company(
        self, *, cik: str | None = None, company_name: str | None = None
    ) -> list[int]: ...

    def get_extraction(self, extraction_id: int) -> FinancialStatement | None: ...


class PivotExportPort(Protocol):
    """Driven port: serialize several FinancialStatements (e.g. one per
    selected fiscal year) into a single combined/pivoted export - rows are
    line items (grouped by category), columns are periods. Distinct from
    ExportPort since the shape (many statements -> bytes) differs."""

    def export(self, statements: list[FinancialStatement]) -> bytes: ...
