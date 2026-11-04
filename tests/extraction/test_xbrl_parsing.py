from finextract.extraction.domain.models import XbrlFact
from finextract.extraction.infrastructure.xbrl_parsing import entity_name, parse_xbrl_facts

_FILING = """<xbrl xmlns="http://www.xbrl.org/2003/instance"
    xmlns:xbrldi="http://xbrl.org/2006/xbrldi" xmlns:us-gaap="http://fasb.org/us-gaap/2025"
    xmlns:jpdei_cor="http://disclosure.edinet-fsa.go.jp/jpdei">
  {extra}
  <context id="total">
    <entity><identifier scheme="s">1</identifier></entity>
    <period><startDate>2025-01-01</startDate><endDate>2025-12-31</endDate></period>
  </context>
  <context id="products">
    <entity><identifier scheme="s">1</identifier>
      <segment><xbrldi:explicitMember dimension="a">b</xbrldi:explicitMember></segment>
    </entity>
    <period><startDate>2025-01-01</startDate><endDate>2025-12-31</endDate></period>
  </context>
  <context id="Year_NonConsolidatedMember">
    <entity><identifier scheme="s">1</identifier></entity>
    <period><startDate>2025-01-01</startDate><endDate>2025-12-31</endDate></period>
    <scenario><xbrldi:explicitMember dimension="c">d</xbrldi:explicitMember></scenario>
  </context>
  <us-gaap:Revenues contextRef="products">70</us-gaap:Revenues>
  <us-gaap:Revenues contextRef="total">100</us-gaap:Revenues>
  <us-gaap:Revenues contextRef="Year_NonConsolidatedMember">40</us-gaap:Revenues>
</xbrl>"""


def _values_with_period(extra: str = "") -> list[str]:
    facts = parse_xbrl_facts(_FILING.format(extra=extra).encode())
    return [f.value for f in facts if f.tag == "us-gaap:Revenues" and f.period_end]


def test_dimensional_facts_get_no_period_so_breakdowns_never_replace_totals() -> None:
    assert _values_with_period() == ["100"]


def test_standalone_edinet_filer_keeps_non_consolidated_statements() -> None:
    dei = (
        '<jpdei_cor:WhetherConsolidatedFinancialStatementsArePreparedDEI contextRef="total">'
        "false</jpdei_cor:WhetherConsolidatedFinancialStatementsArePreparedDEI>"
    )
    assert _values_with_period(dei) == ["100", "40"]


def test_entity_name_prefers_filing_cover_page_and_falls_back() -> None:
    fact = XbrlFact(tag="dei:EntityRegistrantName", value="Apple Inc.", context_ref="c")
    assert entity_name([fact], "https://sec.gov/x") == "Apple Inc."
    assert entity_name([], "https://sec.gov/x") == "https://sec.gov/x"
