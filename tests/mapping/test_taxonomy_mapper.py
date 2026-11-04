from datetime import date

from finextract.export.infrastructure.statement_template import load_statement_template
from finextract.extraction.domain.models import RawFiling, XbrlFact
from finextract.mapping.infrastructure.taxonomy_mapper import (
    DEFAULT_TAG_MAP,
    TagTableTaxonomyMapper,
)

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


def _normalize(*facts: XbrlFact) -> list:
    raw_filing = RawFiling(
        company_identifier="ACME",
        company_name="Acme Corp",
        source_url="fixture://acme.xbrl",
        facts=list(facts),
    )
    return TagTableTaxonomyMapper().normalize(raw_filing)


def test_year_ending_in_early_january_belongs_to_the_prior_fiscal_year() -> None:
    statements = _normalize(
        XbrlFact(
            tag="us-gaap:Revenues",
            value="80",
            context_ref="fy22",
            period_start=date(2022, 1, 3),
            period_end=date(2023, 1, 1),
        ),
        XbrlFact(
            tag="us-gaap:Revenues",
            value="85",
            context_ref="fy23",
            period_start=date(2023, 1, 2),
            period_end=date(2023, 12, 31),
        ),
    )

    assert [(s.fiscal_period.period_label, s.get("revenue").value) for s in statements] == [
        ("FY2022", 80),
        ("FY2023", 85),
    ]


def test_one_value_per_field_prefers_listed_tag_then_precision() -> None:
    statements = _normalize(
        XbrlFact(
            tag="us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax",
            value="706",
            context_ref="c1",
            **_PERIOD,
        ),
        XbrlFact(tag="us-gaap:Revenues", value="713", context_ref="c1", **_PERIOD),
        XbrlFact(
            tag="us-gaap:NetIncomeLoss", value="100", decimals=-2, context_ref="c1", **_PERIOD
        ),
        XbrlFact(tag="us-gaap:NetIncomeLoss", value="96", decimals=0, context_ref="c1", **_PERIOD),
    )

    statement = statements[0]
    assert len(statement.line_items) == 2
    assert statement.get("revenue").value == 713
    assert statement.get("revenue").original_label == "us-gaap:Revenues"
    assert statement.get("net_income").value == 96


def test_ifrs_filer_gets_all_three_statements() -> None:
    instant = {"period_start": date(2023, 12, 31), "period_end": date(2023, 12, 31)}
    statements = _normalize(
        XbrlFact(tag="ifrs-full:ProfitLoss", value="110", context_ref="c1", **_PERIOD),
        XbrlFact(
            tag="ifrs-full:ProfitLossAttributableToOwnersOfParent",
            value="100",
            context_ref="c1",
            **_PERIOD,
        ),
        XbrlFact(
            tag="ifrs-full:CashFlowsFromUsedInOperatingActivities",
            value="50",
            context_ref="c1",
            **_PERIOD,
        ),
        XbrlFact(tag="ifrs-full:Assets", value="900", context_ref="c2", **instant),
    )

    fiscal_year, balance_sheet = sorted(statements, key=lambda s: s.fiscal_period.period_label)[
        ::-1
    ]
    assert fiscal_year.get("net_income").value == 100
    assert fiscal_year.get("cash_flow_operating").value == 50
    assert balance_sheet.get("total_assets").value == 900


def test_ifrs_fields_use_the_statement_template_names() -> None:
    known = {(row.category, row.standard_field) for row in load_statement_template()}
    # Reported, but deliberately outside the Bloomberg-style template.
    extras = {"deferred_tax_assets", "eps_basic", "eps_diluted"} | {
        "shares_outstanding_basic",
        "shares_outstanding_diluted",
    }

    unknown = {
        field
        for tag, (field, category) in DEFAULT_TAG_MAP.items()
        if tag.startswith("ifrs-full:") and (category, field) not in known and field not in extras
    }

    assert unknown == set()
