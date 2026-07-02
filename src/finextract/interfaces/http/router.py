from __future__ import annotations

from fastapi import APIRouter, HTTPException, Response

from finextract.export.application.export_statement import ExportStatement
from finextract.export.infrastructure.csv_exporter import CsvExporter
from finextract.export.infrastructure.excel_exporter import ExcelExporter
from finextract.extraction.domain.ports import FilingDirectoryPort
from finextract.interfaces.http.schemas import (
    CompanySummaryResponse,
    ExportFormat,
    FilingSummaryResponse,
    FinancialStatementResponse,
    LineItemResponse,
)
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
    normalize_statement: NormalizeStatement,
    *,
    remote_normalize_statement: NormalizeStatement | None = None,
    filing_directory: FilingDirectoryPort | None = None,
) -> APIRouter:
    """Composition-root-provided use cases/ports are injected here rather
    than constructed in this module, keeping the HTTP layer free of adapter
    wiring (a driving adapter should only call into application use cases).

    `normalize_statement` drives the local-fixture flow (dev/testing).
    `remote_normalize_statement` + `filing_directory` drive the SEC EDGAR
    flow (search company -> list filings -> process one); both are optional
    so the router still works in environments without SEC access configured.
    """

    @router.post("/filings/extract", response_model=None)
    def extract_filing(
        company_identifier: str, format: ExportFormat = ExportFormat.JSON
    ) -> FinancialStatementResponse | Response:
        try:
            statement = normalize_statement(company_identifier)
        except SourceNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
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

    return router
