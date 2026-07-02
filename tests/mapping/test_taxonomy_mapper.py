from finextract.extraction.domain.models import RawFiling, XbrlFact
from finextract.mapping.infrastructure.taxonomy_mapper import TagTableTaxonomyMapper


def test_normalize_maps_known_tags_and_drops_unknown() -> None:
    raw_filing = RawFiling(
        company_identifier="ACME",
        company_name="Acme Corp",
        source_url="fixture://acme.xbrl",
        facts=[
            XbrlFact(tag="us-gaap:Revenues", value="1000.5", context_ref="c1"),
            XbrlFact(tag="us-gaap:NetIncomeLoss", value="200", context_ref="c1"),
            XbrlFact(tag="unmapped:SomeTag", value="42", context_ref="c1"),
        ],
    )
    mapper = TagTableTaxonomyMapper()

    statement = mapper.normalize(raw_filing)

    assert statement.company_name == "Acme Corp"
    assert len(statement.line_items) == 2
    revenue = statement.get("revenue")
    assert revenue is not None
    assert revenue.value == 1000.5
    assert statement.get("net_income").value == 200
    assert statement.get("unmapped_field") is None
