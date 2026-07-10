from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, File, HTTPException, Query, Response, UploadFile

from finextract.export.application.export_combined_statements import ExportCombinedStatements
from finextract.export.application.export_statement import ExportStatement
from finextract.export.domain.ports import ExtractionPersisterPort, ExtractionQueryPort
from finextract.export.infrastructure.csv_exporter import CsvExporter
from finextract.export.infrastructure.excel_exporter import ExcelExporter
from finextract.export.infrastructure.pivot_exporter import PivotCsvExporter, PivotExcelExporter
from finextract.extraction.domain.ports import FilingDirectoryPort
from finextract.interfaces.http.schemas import (
    CompanySummaryResponse,
    ExportFormat,
    ExtractionSummaryResponse,
    FilingSummaryResponse,
    FinancialStatementResponse,
    LineItemResponse,
)
from finextract.mapping.application.extract_uploaded_filing import ExtractUploadedFiling
from finextract.mapping.application.normalize_statement import NormalizeStatement
from finextract.mapping.domain.models import FinancialStatement
from finextract.shared_kernel.errors import SourceNotFoundError

router = APIRouter()

_EXPORT_MEDIA_TYPES = {
    ExportFormat.CSV: "text/csv",
    ExportFormat.EXCEL: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}


def _to_response(statement: FinancialStatement) -> FinancialStatementResponse:
    return FinancialStatementResponse(
        company_name=statement.company_name,
        fiscal_year=statement.fiscal_period.fiscal_year,
        period_label=statement.fiscal_period.period_label,
        currency=statement.currency.value,
        accounting_standard=statement.accounting_standard.value,
        line_items=[
            LineItemResponse(
                field_name=li.field_name,
                category=li.category.value,
                value=li.value,
                original_label=li.original_label,
                source=li.source,
                page_number=li.page_number,
                confidence_score=li.confidence_score,
            )
            for li in statement.line_items
        ],
    )


def _export_or_serialize(
    statement: FinancialStatement, format: ExportFormat
) -> FinancialStatementResponse | Response:
    if format == ExportFormat.JSON:
        return _to_response(statement)

    exporter = CsvExporter() if format == ExportFormat.CSV else ExcelExporter()
    payload = ExportStatement(exporter)(statement)
    return Response(content=payload, media_type=_EXPORT_MEDIA_TYPES[format])


def _export_or_serialize_many(
    statements: list[FinancialStatement], format: ExportFormat
) -> list[FinancialStatementResponse] | Response:
    if format == ExportFormat.JSON:
        return [_to_response(s) for s in statements]

    exporter = PivotCsvExporter() if format == ExportFormat.CSV else PivotExcelExporter()
    payload = ExportCombinedStatements(exporter)(statements)
    return Response(content=payload, media_type=_EXPORT_MEDIA_TYPES[format])


def build_router(
    *,
    remote_normalize_statements: dict[str, NormalizeStatement] | None = None,
    filing_directories: dict[str, FilingDirectoryPort] | None = None,
    extraction_query: ExtractionQueryPort | None = None,
    extraction_persister: ExtractionPersisterPort | None = None,
    extract_uploaded_filing: ExtractUploadedFiling | None = None,
) -> APIRouter:
    """Composition-root-provided use cases/ports are injected here rather
    than constructed in this module, keeping the HTTP layer free of adapter
    wiring (a driving adapter should only call into application use cases).

    `remote_normalize_statements` + `filing_directories` are keyed by a
    short source id ("sec-edgar", "edinet", ...) and drive the
    search-company -> list-filings -> process-one flow for each configured
    government XBRL source; `extract_uploaded_filing` drives the
    user-uploaded-file flow. Both dicts default empty so the router still
    works in environments without any remote source / persistence
    configured. A filing can yield several FinancialStatements (one per
    comparative fiscal year/period found), so extraction endpoints return
    lists.
    """
    directories = filing_directories or {}
    normalizers = remote_normalize_statements or {}

    def _get_directory(source: str) -> FilingDirectoryPort:
        directory = directories.get(source)
        if directory is None:
            raise HTTPException(status_code=503, detail=f"Filing source '{source}' not configured")
        return directory

    def _get_normalizer(source: str) -> NormalizeStatement:
        normalizer = normalizers.get(source)
        if normalizer is None:
            raise HTTPException(status_code=503, detail=f"Filing source '{source}' not configured")
        return normalizer

    @router.post("/filings/upload", response_model=None)
    async def upload_filing(
        file: Annotated[UploadFile, File()],
        format: ExportFormat = ExportFormat.JSON,
        label: str | None = None,
    ) -> list[FinancialStatementResponse] | Response:
        if extract_uploaded_filing is None:
            raise HTTPException(status_code=503, detail="Upload extraction not configured")
        content = await file.read()
        filename = file.filename or "upload.xbrl"
        statements = extract_uploaded_filing(filename, content)
        if extraction_persister is not None:
            for statement in statements:
                extraction_persister.persist(
                    statement, f"upload:{filename}", label=label or filename
                )
        return _export_or_serialize_many(statements, format)

    @router.get("/sources")
    def list_sources() -> list[str]:
        return sorted(set(directories) | set(normalizers))

    @router.get("/companies/search")
    def search_companies(q: str, source: str = "sec-edgar") -> list[CompanySummaryResponse]:
        return [
            CompanySummaryResponse(
                identifier=c.identifier, name=c.name, source=c.source, ticker=c.ticker
            )
            for c in _get_directory(source).search_companies(q)
        ]

    @router.get("/companies/{identifier}/filings")
    def list_filings(
        identifier: str, source: str = "sec-edgar", lookback_days: int | None = None
    ) -> list[FilingSummaryResponse]:
        """`lookback_days` only affects sources that scan a rolling window
        (currently EDINET, which has no per-company filing list endpoint);
        sources with a real per-company endpoint (SEC EDGAR) ignore it and
        always return full recent history in one call. Pass a larger value
        to page further back ("load more" in the UI) - already-scanned days
        are cached, so this only pays for the newly-widened window."""
        try:
            filings = _get_directory(source).list_filings(identifier, lookback_days=lookback_days)
        except SourceNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return [
            FilingSummaryResponse(
                accession_number=f.accession_number,
                form_type=f.form_type,
                filing_date=f.filing_date,
                document_url=f.document_url,
            )
            for f in filings
        ]

    @router.post("/filings/process", response_model=None)
    def process_filing(
        document_url: str,
        source: str = "sec-edgar",
        cik: str | None = None,
        ticker: str | None = None,
        label: str | None = None,
        format: ExportFormat = ExportFormat.JSON,
    ) -> list[FinancialStatementResponse] | Response:
        """Process one filing picked from list_filings' results, by its
        document_url, against the given `source` adapter. This is the
        "click it to process it" step. `cik`/`ticker` are known by the
        caller from the preceding search/list_filings steps and are
        persisted alongside the extraction for company-level lookups (e.g.
        /extractions/combine?cik=...). `label` is an optional human-friendly
        name (e.g. "AAPL 10-Q - filed 2025-08-01") the caller builds from
        data it already has (company + form_type + filing_date), stored so
        the extraction history doesn't have to show the raw XBRL
        document_url."""
        try:
            statements = _get_normalizer(source)(document_url)
        except SourceNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        if extraction_persister is not None:
            for statement in statements:
                extraction_persister.persist(
                    statement, document_url, cik=cik, ticker=ticker, label=label
                )
        return _export_or_serialize_many(statements, format)

    @router.get("/extractions")
    def list_extractions(
        company_identifier: str | None = None, source_reference: str | None = None
    ) -> list[ExtractionSummaryResponse]:
        if extraction_query is None:
            raise HTTPException(status_code=503, detail="Extraction history not configured")
        return [
            ExtractionSummaryResponse(
                id=e.id,
                company_name=e.company_name,
                fiscal_year=e.fiscal_year,
                period_label=e.period_label,
                currency=e.currency,
                accounting_standard=e.accounting_standard,
                source_reference=e.source_reference,
                extracted_at=e.extracted_at,
                label=e.label,
            )
            for e in extraction_query.list_extractions(
                company_identifier=company_identifier, source_reference=source_reference
            )
        ]

    @router.get("/extractions/combine", response_model=None)
    def combine_extractions(
        ids: Annotated[list[int] | None, Query()] = None,
        cik: str | None = None,
        company_name: str | None = None,
        format: ExportFormat = ExportFormat.JSON,
    ) -> list[FinancialStatementResponse] | Response:
        """Combine several previously persisted extractions into one pivoted
        view/export. Either pass explicit `ids`, or `cik`/`company_name` to
        pull every fiscal year persisted for that company in one call."""
        if extraction_query is None:
            raise HTTPException(status_code=503, detail="Extraction history not configured")
        resolved_ids = ids or []
        if not resolved_ids and (cik or company_name):
            resolved_ids = extraction_query.get_extraction_ids_for_company(
                cik=cik, company_name=company_name
            )
            if not resolved_ids:
                raise HTTPException(status_code=404, detail="No extractions found for company")
        statements = []
        for extraction_id in resolved_ids:
            statement = extraction_query.get_extraction(extraction_id)
            if statement is None:
                raise HTTPException(status_code=404, detail=f"Extraction {extraction_id} not found")
            statements.append(statement)
        return _export_or_serialize_many(statements, format)

    @router.get("/extractions/{extraction_id}", response_model=None)
    def get_extraction(
        extraction_id: int, format: ExportFormat = ExportFormat.JSON
    ) -> FinancialStatementResponse | Response:
        if extraction_query is None:
            raise HTTPException(status_code=503, detail="Extraction history not configured")
        statement = extraction_query.get_extraction(extraction_id)
        if statement is None:
            raise HTTPException(status_code=404, detail="Extraction not found")
        return _export_or_serialize(statement, format)

    return router
