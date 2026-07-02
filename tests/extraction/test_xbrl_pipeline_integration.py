"""End-to-end: fixture XBRL file -> extract -> map -> CSV export."""

from pathlib import Path

from finextract.export.infrastructure.csv_exporter import CsvExporter
from finextract.extraction.infrastructure.xbrl_adapter import LocalXbrlFileAdapter
from finextract.mapping.application.normalize_statement import NormalizeStatement
from finextract.mapping.infrastructure.taxonomy_mapper import TagTableTaxonomyMapper

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


def test_pipeline_end_to_end() -> None:
    normalize_statement = NormalizeStatement(
        source=LocalXbrlFileAdapter(filings_dir=FIXTURES_DIR),
        mapper=TagTableTaxonomyMapper(),
    )

    statement = normalize_statement("acme")
    csv_bytes = CsvExporter().export(statement)

    assert statement.get("revenue") is not None
    assert b"revenue" in csv_bytes
