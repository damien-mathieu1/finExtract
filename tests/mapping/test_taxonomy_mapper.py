from datetime import date

from finextract.extraction.domain.models import RawFiling, XbrlFact
from finextract.mapping.infrastructure.taxonomy_mapper import TagTableTaxonomyMapper

_PERIOD = {"period_start": date(2023, 1, 1), "period_end": date(2023, 12, 31)}


def test_normalize_maps_known_tags_and_drops_unknown() -> None:
    raw_filing = RawFiling(
        company_identifier="ACME",
        company_name="Acme Corp",
        source_url="fixture://acme.xbrl",
        facts=[
            XbrlFact(tag="us-gaap:Revenues", value="1000.5", context_ref="c1", **_PERIOD),
            XbrlFact(tag="us-gaap:NetIncomeLoss", value="200", context_ref="c1", **_PERIOD),
            XbrlFact(tag="unmapped:SomeTag", value="42", context_ref="c1", **_PERIOD),
        ],
    )
    mapper = TagTableTaxonomyMapper()

    statements = mapper.normalize(raw_filing)

    assert len(statements) == 1
    statement = statements[0]
    assert statement.company_name == "Acme Corp"
    assert statement.fiscal_period.fiscal_year == 2023
    assert len(statement.line_items) == 2
    revenue = statement.get("revenue")
    assert revenue is not None
    assert revenue.value == 1000.5
    assert statement.get("net_income").value == 200
    assert statement.get("unmapped_field") is None


def test_normalize_splits_facts_by_distinct_period() -> None:
    raw_filing = RawFiling(
        company_identifier="ACME",
        company_name="Acme Corp",
        source_url="fixture://acme.xbrl",
        facts=[
            XbrlFact(
                tag="us-gaap:Revenues",
                value="1000",
                context_ref="c2023",
                period_start=date(2023, 1, 1),
                period_end=date(2023, 12, 31),
            ),
            XbrlFact(
                tag="us-gaap:Revenues",
                value="900",
                context_ref="c2022",
                period_start=date(2022, 1, 1),
                period_end=date(2022, 12, 31),
            ),
        ],
    )
    mapper = TagTableTaxonomyMapper()

    statements = mapper.normalize(raw_filing)

    assert [s.fiscal_period.fiscal_year for s in statements] == [2022, 2023]
    assert statements[0].get("revenue").value == 900
    assert statements[1].get("revenue").value == 1000


def test_normalize_drops_facts_with_unresolved_period() -> None:
    raw_filing = RawFiling(
        company_identifier="ACME",
        company_name="Acme Corp",
        source_url="fixture://acme.xbrl",
        facts=[XbrlFact(tag="us-gaap:Revenues", value="1000", context_ref="unresolved")],
    )
    mapper = TagTableTaxonomyMapper()

    statements = mapper.normalize(raw_filing)

    assert statements == []
