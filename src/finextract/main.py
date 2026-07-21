from __future__ import annotations

import logging
import os
from collections.abc import Callable
from typing import cast

from fastapi import FastAPI, Request

from finextract.export.domain.ports import ExtractionPersisterPort, ExtractionQueryPort
from finextract.export.infrastructure.postgres_repository import PostgresExporter
from finextract.extraction.domain.ports import FilingDirectoryPort
from finextract.extraction.infrastructure.edinet_adapter import EdinetClient
from finextract.extraction.infrastructure.sec_edgar_adapter import SecEdgarClient
from finextract.interfaces.http.auth import ClerkTokenVerifier
from finextract.interfaces.http.router import build_router
from finextract.mapping.application.extract_uploaded_filing import ExtractUploadedFiling
from finextract.mapping.application.normalize_statement import NormalizeStatement
from finextract.mapping.infrastructure.taxonomy_mapper import (
    DEFAULT_TAG_MAP,
    EDINET_TAG_MAP,
    TagTableTaxonomyMapper,
)
from finextract.shared_kernel.value_objects import Currency, ReportingStandard

SEC_EDGAR_USER_AGENT = os.environ.get("SEC_EDGAR_USER_AGENT")
EDINET_API_KEY = os.environ.get("EDINET_API_KEY")
DATABASE_URL = os.environ.get("DATABASE_URL")
CLERK_ISSUER = os.environ.get("CLERK_ISSUER")
CLERK_AUTHORIZED_PARTIES = os.environ.get("CLERK_AUTHORIZED_PARTIES")
DAILY_EXTRACTION_QUOTA = int(os.environ.get("DAILY_EXTRACTION_QUOTA", "20"))
AUTH_DISABLED = os.environ.get("AUTH_DISABLED", "").lower() in ("1", "true", "yes")

# Composition root: wire concrete adapters into use cases via constructor
# injection. Each government XBRL source gets its own FilingDirectoryPort +
# NormalizeStatement pair, registered under a short source id; the router
# dispatches on that id (?source=edinet, etc). Every source is optional so
# the app still runs with only whichever sources are configured.
default_taxonomy_mapper = TagTableTaxonomyMapper(tag_map=dict(DEFAULT_TAG_MAP))

extract_uploaded_filing = ExtractUploadedFiling(mapper=default_taxonomy_mapper)

postgres_exporter = PostgresExporter(database_url=DATABASE_URL) if DATABASE_URL else None


def _build_verify_user() -> Callable[[Request], str]:
    """The API's Cloud Run URL is publicly invokable, so it must verify
    Clerk JWTs itself rather than trust the frontend proxy. Fail closed:
    refuse to start without an issuer unless auth is explicitly disabled
    for local development."""
    if AUTH_DISABLED:
        logging.getLogger(__name__).warning(
            "AUTH_DISABLED is set: all requests run as 'local-dev-user'. "
            "Never enable this in a deployed environment."
        )

        def _dev_user(request: Request) -> str:
            return "local-dev-user"

        return _dev_user
    if not CLERK_ISSUER:
        raise RuntimeError(
            "CLERK_ISSUER is required (or set AUTH_DISABLED=true for local dev): "
            "the API is publicly reachable and must verify Clerk JWTs itself."
        )
    authorized_parties = (
        [p.strip() for p in CLERK_AUTHORIZED_PARTIES.split(",") if p.strip()]
        if CLERK_AUTHORIZED_PARTIES
        else None
    )
    return ClerkTokenVerifier(issuer=CLERK_ISSUER, authorized_parties=authorized_parties)


verify_user = _build_verify_user()

filing_directories: dict[str, FilingDirectoryPort] = {}
remote_normalize_statements: dict[str, NormalizeStatement] = {}

# SEC EDGAR (US): optional, only wired up if a User-Agent is configured (SEC
# rejects unidentified requests).
if SEC_EDGAR_USER_AGENT:
    sec_edgar_client = SecEdgarClient(user_agent=SEC_EDGAR_USER_AGENT)
    filing_directories["sec-edgar"] = sec_edgar_client
    remote_normalize_statements["sec-edgar"] = NormalizeStatement(
        source=sec_edgar_client, mapper=default_taxonomy_mapper
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
    remote_normalize_statements["edinet"] = NormalizeStatement(
        source=edinet_client, mapper=edinet_taxonomy_mapper
    )

app = FastAPI(title="FinExtract", version="0.1.0")
app.include_router(
    build_router(
        verify_user=verify_user,
        remote_normalize_statements=remote_normalize_statements,
        filing_directories=filing_directories,
        extraction_query=cast(ExtractionQueryPort, postgres_exporter)
        if postgres_exporter is not None
        else None,
        extraction_persister=cast(ExtractionPersisterPort, postgres_exporter)
        if postgres_exporter is not None
        else None,
        extract_uploaded_filing=extract_uploaded_filing,
        daily_extraction_quota=DAILY_EXTRACTION_QUOTA,
    )
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
