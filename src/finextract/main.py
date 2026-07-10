from __future__ import annotations

import os
from typing import cast

from fastapi import FastAPI

from finextract.export.domain.ports import ExtractionPersisterPort, ExtractionQueryPort
from finextract.export.infrastructure.postgres_repository import PostgresExporter
from finextract.extraction.domain.ports import FilingDirectoryPort
from finextract.extraction.infrastructure.edinet_adapter import EdinetClient
from finextract.extraction.infrastructure.sec_edgar_adapter import SecEdgarClient
from finextract.interfaces.http.router import build_router
from finextract.mapping.application.extract_uploaded_filing import ExtractUploadedFiling
from finextract.mapping.application.normalize_statement import NormalizeStatement
from finextract.mapping.application.persist_and_normalize_statement import (
    PersistAndNormalizeStatement,
)
from finextract.mapping.infrastructure.taxonomy_mapper import (
    DEFAULT_TAG_MAP,
    EDINET_TAG_MAP,
    TagTableTaxonomyMapper,
)
from finextract.shared_kernel.value_objects import Currency, ReportingStandard

SEC_EDGAR_USER_AGENT = os.environ.get("SEC_EDGAR_USER_AGENT")
EDINET_API_KEY = os.environ.get("EDINET_API_KEY")
DATABASE_URL = os.environ.get("DATABASE_URL")

# Composition root: wire concrete adapters into use cases via constructor
# injection. Each government XBRL source gets its own FilingDirectoryPort +
# NormalizeStatement pair, registered under a short source id; the router
# dispatches on that id (?source=edinet, etc). Every source is optional so
# the app still runs with only whichever sources are configured.
default_taxonomy_mapper = TagTableTaxonomyMapper(tag_map=dict(DEFAULT_TAG_MAP))

extract_uploaded_filing = ExtractUploadedFiling(mapper=default_taxonomy_mapper)

postgres_exporter = PostgresExporter(database_url=DATABASE_URL) if DATABASE_URL else None


def _wrap_with_persistence(normalizer: NormalizeStatement) -> NormalizeStatement:
    """Extraction history is optional: only wraps the use case if a database
    is configured, so the app still runs (without persistence/history) in
    environments without Postgres. When present, every successful remote
    extraction is recorded as a side effect, independent of the export
    format the caller also requested; the upload flow persists explicitly
    in the router since it isn't a NormalizeStatement."""
    if postgres_exporter is None:
        return normalizer
    return cast(
        NormalizeStatement,
        PersistAndNormalizeStatement(inner=normalizer, persister=postgres_exporter),
    )


filing_directories: dict[str, FilingDirectoryPort] = {}
remote_normalize_statements: dict[str, NormalizeStatement] = {}

# SEC EDGAR (US): optional, only wired up if a User-Agent is configured (SEC
# rejects unidentified requests).
if SEC_EDGAR_USER_AGENT:
    sec_edgar_client = SecEdgarClient(user_agent=SEC_EDGAR_USER_AGENT)
    filing_directories["sec-edgar"] = sec_edgar_client
    remote_normalize_statements["sec-edgar"] = _wrap_with_persistence(
        NormalizeStatement(source=sec_edgar_client, mapper=default_taxonomy_mapper)
    )

# EDINET (Japan): optional, only wired up if an API key is configured.
if EDINET_API_KEY:
    edinet_client = EdinetClient(api_key=EDINET_API_KEY)
    edinet_taxonomy_mapper = TagTableTaxonomyMapper(
        tag_map=dict(EDINET_TAG_MAP),
        currency=Currency.JPY,
        standard=ReportingStandard.JAPANESE_GAAP,
    )
    filing_directories["edinet"] = edinet_client
    remote_normalize_statements["edinet"] = _wrap_with_persistence(
        NormalizeStatement(source=edinet_client, mapper=edinet_taxonomy_mapper)
    )

app = FastAPI(title="FinExtract", version="0.1.0")
app.include_router(
    build_router(
        remote_normalize_statements=remote_normalize_statements,
        filing_directories=filing_directories,
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
