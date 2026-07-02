from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI

from finextract.extraction.infrastructure.sec_edgar_adapter import SecEdgarClient
from finextract.extraction.infrastructure.xbrl_adapter import LocalXbrlFileAdapter
from finextract.interfaces.http.router import build_router
from finextract.mapping.application.normalize_statement import NormalizeStatement
from finextract.mapping.infrastructure.taxonomy_mapper import TagTableTaxonomyMapper

FILINGS_DIR = Path(os.environ.get("FILINGS_DIR", "/app/fixtures"))
SEC_EDGAR_USER_AGENT = os.environ.get("SEC_EDGAR_USER_AGENT")

# Composition root: wire concrete adapters into use cases via constructor
# injection. Swapping the XBRL adapter for a PDF/OCR adapter later only
# touches this function.
taxonomy_mapper = TagTableTaxonomyMapper()

local_source = LocalXbrlFileAdapter(filings_dir=FILINGS_DIR)
normalize_statement = NormalizeStatement(source=local_source, mapper=taxonomy_mapper)

# SEC EDGAR flow is optional: only wired up if a User-Agent is configured
# (SEC rejects unidentified requests), so the app still runs without it.
sec_edgar_client = SecEdgarClient(user_agent=SEC_EDGAR_USER_AGENT) if SEC_EDGAR_USER_AGENT else None
remote_normalize_statement = (
    NormalizeStatement(source=sec_edgar_client, mapper=taxonomy_mapper)
    if sec_edgar_client
    else None
)

app = FastAPI(title="FinExtract", version="0.1.0")
app.include_router(
    build_router(
        normalize_statement,
        remote_normalize_statement=remote_normalize_statement,
        filing_directory=sec_edgar_client,
    )
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
