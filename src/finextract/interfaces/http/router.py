from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, File, HTTPException, Response, UploadFile

from finextract.export.application.export_statement import ExportStatement
from finextract.export.domain.ports import ExtractionPersisterPort, ExtractionQueryPort
from finextract.export.infrastructure.csv_exporter import CsvExporter
from finextract.export.infrastructure.excel_exporter import ExcelExporter
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


def build_router(
    *,
    remote_normalize_statement: NormalizeStatement | None = None,
    filing_directory: FilingDirectoryPort | None = None,
    extraction_query: ExtractionQueryPort | None = None,
    extraction_persister: ExtractionPersisterPort | None = None,
    extract_uploaded_filing: ExtractUploadedFiling | None = None,
) -> APIRouter:
    """Composition-root-provided use cases/ports are injected here rather
    than constructed in this module, keeping the HTTP layer free of adapter
    wiring (a driving adapter should only call into application use cases).

    `remote_normalize_statement` + `filing_directory` drive the SEC EDGAR
    flow (search company -> list filings -> process one); `extract_uploaded_filing`
    drives the user-uploaded-file flow. Both are optional so the router
    still works in environments without SEC access / persistence configured.
    """

    @router.post("/filings/upload", response_model=None)
    async def upload_filing(
        file: Annotated[UploadFile, File()], format: ExportFormat = ExportFormat.JSON
    ) -> FinancialStatementResponse | Response:
        if extract_uploaded_filing is None:
            raise HTTPException(status_code=503, detail="Upload extraction not configured")
        content = await file.read()
        filename = file.filename or "upload.xbrl"
        statement = extract_uploaded_filing(filename, content)
        if extraction_persister is not None:
            extraction_persister.persist(statement, f"upload:{filename}")
        return _export_or_serialize(statement, format)

    @router.get("/companies/search")
    def search_companies(q: str) -> list[CompanySummaryResponse]:
        if filing_directory is None:
            raise HTTPException(status_code=503, detail="SEC EDGAR lookup not configured")
        return [
            CompanySummaryResponse(cik=c.cik, name=c.name, ticker=c.ticker)
            for c in filing_directory.search_companies(q)
        ]

    @router.get("/companies/{cik}/filings")
    def list_filings(cik: str) -> list[FilingSummaryResponse]:
        if filing_directory is None:
            raise HTTPException(status_code=503, detail="SEC EDGAR lookup not configured")
        try:
            filings = filing_directory.list_filings(cik)
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
        document_url: str, format: ExportFormat = ExportFormat.JSON
    ) -> FinancialStatementResponse | Response:
        """Process one filing picked from list_filings' results, by its
        document_url. This is the "click it to process it" step."""
        if remote_normalize_statement is None:
            raise HTTPException(status_code=503, detail="SEC EDGAR lookup not configured")
        try:
            statement = remote_normalize_statement(document_url)
        except SourceNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return _export_or_serialize(statement, format)

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
            )
            for e in extraction_query.list_extractions(
                company_identifier=company_identifier, source_reference=source_reference
            )
        ]

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
