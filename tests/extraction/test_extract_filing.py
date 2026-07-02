from finextract.extraction.application.extract_filing import ExtractFiling
from finextract.extraction.domain.models import RawFiling, XbrlFact


class FakeFilingSource:
    def __init__(self, filing: RawFiling) -> None:
        self._filing = filing

    def fetch_raw_facts(self, company_identifier: str) -> RawFiling:
        assert company_identifier == self._filing.company_identifier
        return self._filing


def test_extract_filing_delegates_to_source() -> None:
    filing = RawFiling(
        company_identifier="ACME",
        company_name="Acme Corp",
        source_url="fixture://acme.xbrl",
        facts=[XbrlFact(tag="us-gaap:Revenues", value="1000", context_ref="c1")],
    )
    use_case = ExtractFiling(source=FakeFilingSource(filing))

    result = use_case("ACME")

    assert result.company_name == "Acme Corp"
    assert result.facts[0].tag == "us-gaap:Revenues"
