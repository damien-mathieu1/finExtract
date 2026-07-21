from __future__ import annotations

from datetime import datetime
from typing import Protocol

from finextract.export.domain.models import ExtractionSummary
from finextract.mapping.domain.models import FinancialStatement


class ExportPort(Protocol):
    """Driven port: persist/serialize a FinancialStatement (Load stage)."""

    def export(self, statement: FinancialStatement) -> bytes: ...


class ExtractionPersisterPort(Protocol):
    """Driven port: record a normalized FinancialStatement as history, keyed
    by the source_reference it was extracted from and the owning user.
    Re-persisting the same (owner, source_reference) upserts (replaces line
    items, bumps extracted_at) rather than accumulating duplicate history
    rows."""

    def persist(
        self,
        statement: FinancialStatement,
        source_reference: str,
        *,
        owner_id: str,
        cik: str | None = None,
        ticker: str | None = None,
        label: str | None = None,
    ) -> None: ...


class ExtractionQueryPort(Protocol):
    """Driven port: query previously persisted extractions. All reads are
    scoped to an owner so users only ever see their own history."""

    def list_extractions(
        self,
        *,
        owner_id: str,
        company_identifier: str | None = None,
        source_reference: str | None = None,
    ) -> list[ExtractionSummary]: ...

    def get_extraction_ids_for_company(
        self, *, owner_id: str, cik: str | None = None, company_name: str | None = None
    ) -> list[int]: ...

    def get_extraction(self, extraction_id: int, *, owner_id: str) -> FinancialStatement | None: ...

    def count_extractions_since(self, *, owner_id: str, since: datetime) -> int: ...


class PivotExportPort(Protocol):
    """Driven port: serialize several FinancialStatements (e.g. one per
    selected fiscal year) into a single combined/pivoted export - rows are
    line items (grouped by category), columns are periods. Distinct from
    ExportPort since the shape (many statements -> bytes) differs."""

    def export(self, statements: list[FinancialStatement]) -> bytes: ...
