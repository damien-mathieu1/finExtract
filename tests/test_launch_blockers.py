from datetime import date

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from finextract.export.infrastructure.pivot_exporter import build_pivot_dataframe
from finextract.extraction.domain.models import RawFiling, XbrlFact
from finextract.extraction.infrastructure.edinet_adapter import EdinetClient
from finextract.extraction.infrastructure.sec_edgar_adapter import SecEdgarClient
from finextract.extraction.infrastructure.xbrl_parsing import parse_xbrl_facts
from finextract.interfaces.http import router as router_module
from finextract.mapping.application.extract_uploaded_filing import ExtractUploadedFiling
from finextract.mapping.domain.models import FinancialStatement, LineItem
from finextract.mapping.infrastructure.taxonomy_mapper import (
    EDINET_TAG_MAP,
    TagTableTaxonomyMapper,
    _fiscal_period_for,
)
from finextract.shared_kernel.errors import SourceNotFoundError
from finextract.shared_kernel.value_objects import (
    Currency,
    ReportingStandard,
    StatementCategory,
)


@pytest.mark.parametrize(
    "url",
    [
        "http://169.254.169.254/computeMetadata/v1/",
        "http://www.sec.gov/Archives/x.htm",
        "https://www.sec.gov.evil.example/Archives/x.htm",
        "https://www.sec.gov/Archives@evil.example/x.htm",
    ],
)
def test_sec_adapter_refuses_anything_but_edgar_archives(url: str) -> None:
    with pytest.raises(SourceNotFoundError):
        SecEdgarClient(user_agent="test test@example.com").fetch_raw_facts(url)


@pytest.mark.parametrize("doc_id", ["../../secret", "S100ABCD/../x", "s100abcd", ""])
def test_edinet_adapter_refuses_malformed_doc_ids(doc_id: str) -> None:
    with pytest.raises(SourceNotFoundError):
        EdinetClient(api_key="key").fetch_raw_facts(doc_id)


def _upload_client() -> TestClient:
    def verify_user(request: Request) -> str:
        return "user"

    app = FastAPI()
    app.include_router(
        router_module.build_router(
            verify_user=verify_user,
            extract_uploaded_filing=ExtractUploadedFiling(mapper=TagTableTaxonomyMapper()),
        )
    )
    return TestClient(app)


def test_upload_over_the_limit_is_refused(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(router_module, "_MAX_UPLOAD_BYTES", 10)
    response = _upload_client().post("/filings/upload", files={"file": ("a.xbrl", b"x" * 11)})
    assert response.status_code == 413


def test_upload_within_the_limit_is_parsed() -> None:
    response = _upload_client().post("/filings/upload", files={"file": ("a.xbrl", b"<xbrl/>")})
    assert response.status_code == 200


@pytest.mark.parametrize(
    ("start", "end", "label"),
    [
        (date(2026, 3, 29), date(2026, 6, 27), "3M to 2026-06-27"),
        (date(2025, 12, 28), date(2026, 6, 27), "6M to 2026-06-27"),
        (date(2025, 9, 28), date(2026, 6, 27), "9M to 2026-06-27"),
        (date(2025, 9, 28), date(2026, 9, 26), "FY2026"),
        (date(2026, 9, 26), date(2026, 9, 26), "As of 2026-09-26"),
    ],
)
def test_period_labels_state_length_and_end(start: date, end: date, label: str) -> None:
    assert _fiscal_period_for(start, end).period_label == label


def test_currency_comes_from_units_and_skips_per_share() -> None:
    filing = b"""<xbrl xmlns="http://www.xbrl.org/2003/instance" xmlns:a="u">
      <unit id="yen"><measure>iso4217:JPY</measure></unit>
      <unit id="eps"><divide><unitNumerator><measure>iso4217:JPY</measure></unitNumerator>
        <unitDenominator><measure>xbrli:shares</measure></unitDenominator></divide></unit>
      <a:b contextRef="c" unitRef="yen">1</a:b>
      <a:c contextRef="c" unitRef="eps">2</a:c>
    </xbrl>"""
    assert [fact.currency for fact in parse_xbrl_facts(filing)] == ["JPY", None]


def _fact(tag: str, currency: str | None) -> XbrlFact:
    return XbrlFact(
        tag=tag,
        value="1",
        context_ref="c",
        period_start=date(2025, 4, 1),
        period_end=date(2026, 3, 31),
        currency=currency,
    )


def _normalize(facts: list[XbrlFact]) -> FinancialStatement:
    mapper = TagTableTaxonomyMapper(
        tag_map={tag: ("x", StatementCategory.BALANCE_SHEET) for tag in {f.tag for f in facts}}
    )
    return mapper.normalize(RawFiling("id", "name", "url", facts))[0]


def test_standard_and_currency_are_read_from_the_filing() -> None:
    statement = _normalize([_fact("jpigp_cor:Revenue", "JPY"), _fact("ifrs-full:Assets", "JPY")])
    assert statement.currency == Currency.JPY
    assert statement.accounting_standard == ReportingStandard.IFRS


def test_unlisted_currency_is_flagged_not_called_usd() -> None:
    assert _normalize([_fact("us-gaap:Assets", "ZAR")]).currency == Currency.UNKNOWN


def test_mapper_defaults_apply_when_the_filing_says_nothing() -> None:
    statement = _normalize([_fact("custom:Assets", None)])
    assert statement.currency == Currency.USD
    assert statement.accounting_standard == ReportingStandard.US_GAAP


def test_edinet_tag_map_covers_ifrs_filers() -> None:
    assert any(tag.startswith("jpigp_cor:") for tag in EDINET_TAG_MAP)


def _statement(company: str, value: float) -> FinancialStatement:
    return FinancialStatement(
        company_name=company,
        fiscal_period=_fiscal_period_for(date(2025, 1, 1), date(2025, 12, 31)),
        currency=Currency.USD,
        accounting_standard=ReportingStandard.US_GAAP,
        line_items=[
            LineItem(
                field_name="revenue",
                category=StatementCategory.INCOME_STATEMENT,
                value=value,
                original_label="us-gaap:Revenues",
            )
        ],
    )


def test_merged_companies_keep_separate_columns() -> None:
    df = build_pivot_dataframe([_statement("Apple", 1.0), _statement("Microsoft", 2.0)])
    assert df.iloc[0]["Apple FY2025"] == 1.0
    assert df.iloc[0]["Microsoft FY2025"] == 2.0


def test_one_company_keeps_plain_period_columns() -> None:
    assert "FY2025" in build_pivot_dataframe([_statement("Apple", 1.0)]).columns
