# FinExtract

Pulls financial statements out of official company filings (SEC EDGAR for
the US, EDINET for Japan) via their XBRL/iXBRL data, normalizes them into a
common schema across US GAAP / Japanese GAAP / IFRS, and exports clean
CSV/Excel — so you don't have to copy numbers out of a PDF by hand.

FastAPI backend + Next.js frontend, Clerk auth, Postgres for extraction
history.

## How it works

1. **Extract** — fetch a filing's raw XBRL facts (SEC EDGAR, EDINET, or a
   user-uploaded XBRL file).
2. **Map** — translate filer-specific tags (`us-gaap:Revenues`,
   `jppfs_cor:NetSales`, ...) into a standard field set (`revenue`,
   `net_income`, ...) via a static tag lookup table.
3. **Export** — serve the normalized statement as JSON, or as a
   Bloomberg-style CSV/Excel workbook (styled PL/BS/CS sheets, optional
   chart sheet), or persist it to Postgres as extraction history.

## Architecture

DDD bounded contexts with hexagonal (ports & adapters) boundaries, all
inside one FastAPI service — each context could become its own deployable
service later without touching domain logic.

```
src/finextract/
├── shared_kernel/    # cross-context value objects (Currency, FiscalPeriod, ReportingStandard)
├── extraction/       # get raw XBRL facts from a filing
├── mapping/          # normalize raw facts into the standard schema
├── export/           # write the standard schema to CSV/Excel/Postgres
└── interfaces/http/  # FastAPI routes (driving adapter)
```

Each context: `domain/` (entities + `ports.py`, no framework imports) →
`application/` (use cases) → `infrastructure/` (adapters: XBRL parser,
tag map, CSV/Excel/Postgres writers). Infrastructure depends on domain
ports, never the reverse.

`frontend/` is a separate Next.js app (App Router) — filing search, saved
extractions, a data viewer, and charts with Excel export.

## API

- `GET /companies/search?q=apple&source=sec-edgar|edinet` — search companies
- `GET /companies/{identifier}/filings?source=...` — list a company's filings
- `POST /filings/process?document_url=...&source=...&format=json|csv|excel` — extract + persist one filing
- `POST /filings/upload` — same pipeline for a user-uploaded XBRL file
- `GET /extractions` — list saved extractions (owner-scoped)
- `GET /extractions/{id}?format=...` / `GET /extractions/combine?ids=...&format=...` — fetch or export one/many
- `GET /extractions/figures?ids=...&metric=...&chart_type=...` — export with a native Excel chart sheet
- `DELETE /extractions/{id}` / `DELETE /extractions?ids=...` — delete one or many

All routes except `/` and `/sign-in` require a Clerk session; SEC EDGAR
endpoints also need `SEC_EDGAR_USER_AGENT` set (SEC rejects anonymous
requests), EDINET needs `EDINET_API_KEY`. Auto-generated docs at `/docs`.

## Running locally

Quickest path — full stack (Postgres + API + frontend) via Docker:

```bash
cp .env.example .env   # fill in Clerk + SEC/EDINET keys
docker compose up --build
# frontend: http://localhost:3000
# API docs: http://localhost:8000/docs
```

Backend-only, using [uv](https://docs.astral.sh/uv/):

```bash
uv sync
uv run pre-commit install   # one-time: lint/format on every commit
uv run pytest
uv run uvicorn finextract.main:app --reload
```

## Deployment

GCP Cloud Run (api + frontend), provisioned via OpenTofu, deployed on every
GitHub Release via `.github/workflows/deploy.yml`. Postgres is
[Neon](https://neon.tech). Full detail in [`infra/README.md`](infra/README.md).

```bash
cd infra
cp terraform.tfvars.example terraform.tfvars   # fill in real values
tofu init && tofu apply
```

**Before going live**: set up [GCP budget alerts + budget actions](https://cloud.google.com/billing/docs/how-to/budgets) —
actual protection against a runaway bill, unlike a limited-balance card
(which only blocks the charge after the fact).

## Known gaps

- PDF/OCR extraction isn't implemented (XBRL only for now).
- Only extractions made *after* a given tag-map update get the benefit of
  it — the tag map is applied at extraction time, not retroactively on
  re-export, and raw XBRL facts aren't kept, so re-extracting is the only
  way to backfill an older saved extraction.
- Only 10-K/10-Q/20-F/40-F form types are considered on SEC EDGAR.
