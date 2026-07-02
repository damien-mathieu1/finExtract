from __future__ import annotations

import os
from typing import cast

from fastapi import FastAPI

from finextract.export.domain.ports import ExtractionPersisterPort, ExtractionQueryPort
from finextract.export.infrastructure.postgres_repository import PostgresExporter
from finextract.extraction.infrastructure.sec_edgar_adapter import SecEdgarClient
from finextract.interfaces.http.router import build_router
from finextract.mapping.application.extract_uploaded_filing import ExtractUploadedFiling
from finextract.mapping.application.normalize_statement import NormalizeStatement
from finextract.mapping.application.persist_and_normalize_statement import (
    PersistAndNormalizeStatement,
)
from finextract.mapping.infrastructure.taxonomy_mapper import TagTableTaxonomyMapper

SEC_EDGAR_USER_AGENT = os.environ.get("SEC_EDGAR_USER_AGENT")
DATABASE_URL = os.environ.get("DATABASE_URL")

# Composition root: wire concrete adapters into use cases via constructor
# injection. Swapping the XBRL adapter for a PDF/OCR adapter later only
# touches this function.
taxonomy_mapper = TagTableTaxonomyMapper()

extract_uploaded_filing = ExtractUploadedFiling(mapper=taxonomy_mapper)

# SEC EDGAR flow is optional: only wired up if a User-Agent is configured
# (SEC rejects unidentified requests), so the app still runs without it.
sec_edgar_client = SecEdgarClient(user_agent=SEC_EDGAR_USER_AGENT) if SEC_EDGAR_USER_AGENT else None
remote_normalize_statement = (
    NormalizeStatement(source=sec_edgar_client, mapper=taxonomy_mapper)
    if sec_edgar_client
    else None
)

# Extraction history is optional: only wired up if a database is configured,
# so the app still runs (without persistence/history) in environments
# without Postgres. When present, it wraps the SEC-EDGAR normalize use case
# so every successful extraction is recorded as a side effect, independent
# of the export format the caller also requested; the upload flow persists
# explicitly in the router since it isn't a NormalizeStatement.
postgres_exporter = PostgresExporter(database_url=DATABASE_URL) if DATABASE_URL else None
if postgres_exporter is not None and remote_normalize_statement is not None:
    remote_normalize_statement = PersistAndNormalizeStatement(
        inner=remote_normalize_statement, persister=postgres_exporter
    )

app = FastAPI(title="FinExtract", version="0.1.0")
app.include_router(
    build_router(
        remote_normalize_statement=remote_normalize_statement,
        filing_directory=sec_edgar_client,
        extraction_query=cast(ExtractionQueryPort, postgres_exporter)
        if postgres_exporter is not None
        else None,
        extraction_persister=cast(ExtractionPersisterPort, postgres_exporter)
        if postgres_exporter is not None
        else None,
        extract_uploaded_filing=extract_uploaded_filing,
    )
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
