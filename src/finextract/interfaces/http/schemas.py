from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class ExportFormat(StrEnum):
    CSV = "csv"
    EXCEL = "excel"
    JSON = "json"


class ExtractFilingRequest(BaseModel):
    company_identifier: str = Field(..., description="Ticker or CIK identifying the filing")


class CompanySummaryResponse(BaseModel):
    identifier: str
    name: str
    source: str
    ticker: str | None


class FilingSummaryResponse(BaseModel):
    accession_number: str
    form_type: str
    filing_date: str
    document_url: str


class LineItemResponse(BaseModel):
    field_name: str
    category: str
    value: float | None
    original_label: str
    source: str
    page_number: int | None
    confidence_score: float | None


class FinancialStatementResponse(BaseModel):
    company_name: str
    fiscal_year: int
    period_label: str
    currency: str
    accounting_standard: str
    line_items: list[LineItemResponse]


class ExtractionSummaryResponse(BaseModel):
    id: int
    company_name: str
    fiscal_year: int
    period_label: str
    currency: str
    accounting_standard: str
    source_reference: str
    extracted_at: datetime
    label: str | None = None
