from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from finextract.extraction.domain.models import RawFiling, XbrlFact
from finextract.mapping.domain.models import FinancialStatement, LineItem
from finextract.shared_kernel.value_objects import Currency, FiscalPeriod, ReportingStandard

# Maps source taxonomy tags (company wording, via us-gaap/ifrs) to standard
# schema field names. Extend as new tags/wordings are encountered.
DEFAULT_TAG_MAP: dict[str, str] = {
    "us-gaap:Revenues": "revenue",
    "us-gaap:SalesRevenueNet": "revenue",
    "ifrs-full:Revenue": "revenue",
    "us-gaap:CostOfRevenue": "cost_of_revenue",
    "us-gaap:GrossProfit": "gross_profit",
    "us-gaap:OperatingIncomeLoss": "operating_income",
    "us-gaap:IncomeLossFromContinuingOperationsBeforeIncomeTaxes": "profit_before_tax",
    "us-gaap:IncomeTaxExpenseBenefit": "income_tax_expense",
    "us-gaap:NetIncomeLoss": "net_income",
    "ifrs-full:ProfitLoss": "net_income",
    "us-gaap:EarningsPerShareBasic": "eps",
    "us-gaap:CashAndCashEquivalentsAtCarryingValue": "cash_and_equivalents",
    "us-gaap:AccountsReceivableNetCurrent": "accounts_receivable",
    "us-gaap:InventoryNet": "inventory",
    "us-gaap:AssetsCurrent": "total_current_assets",
    "us-gaap:Assets": "total_assets",
    "us-gaap:LiabilitiesCurrent": "total_current_liabilities",
    "us-gaap:Liabilities": "total_liabilities",
    "us-gaap:StockholdersEquity": "total_equity",
    "us-gaap:NetCashProvidedByUsedInOperatingActivities": "cash_flow_operating",
    "us-gaap:NetCashProvidedByUsedInInvestingActivities": "cash_flow_investing",
    "us-gaap:NetCashProvidedByUsedInFinancingActivities": "cash_flow_financing",
    "us-gaap:PaymentsToAcquirePropertyPlantAndEquipment": "capex",
}


@dataclass(slots=True)
class TagTableTaxonomyMapper:
    """TaxonomyMapperPort implementation backed by a static tag lookup table.

    Facts whose tag has no entry in the table are dropped from the standard
    schema but not lost: they stay retrievable from the RawFiling for
    auditing/debugging. A future adapter (e.g. LLM-assisted mapping for PDF
    extraction) implements the same port with fuzzier matching.
    """

    tag_map: dict[str, str] = field(default_factory=lambda: dict(DEFAULT_TAG_MAP))

    def normalize(self, raw_filing: RawFiling) -> FinancialStatement:
        line_items = [
            LineItem(
                field_name=self.tag_map[fact.tag],
                value=_to_float(fact),
                original_label=fact.tag,
                source="XBRL",
            )
            for fact in raw_filing.facts
            if fact.tag in self.tag_map
        ]

        return FinancialStatement(
            company_name=raw_filing.company_name,
            fiscal_period=_unknown_fiscal_period(),
            currency=Currency.USD,
            accounting_standard=ReportingStandard.US_GAAP,
            line_items=line_items,
        )


def _to_float(fact: XbrlFact) -> float | None:
    """Parse an XbrlFact's raw display value into its actual numeric value.

    iXBRL values are display-formatted: thousands separators, an optional
    `scale` multiplier (displayed_value * 10**scale = actual value, e.g.
    "195,201" with scale=6 means $195,201,000,000), and a `sign` attribute
    for negation instead of a leading "-". Plain XBRL facts have none of
    these (scale/sign are None), so this degrades to a plain float parse.
    """
    cleaned = fact.value.replace(",", "").strip()
    if not cleaned:
        return None
    try:
        value = float(cleaned)
    except ValueError:
        return None

    if fact.scale is not None:
        value *= 10**fact.scale
    if fact.sign == "-":
        value = -value
    return value


def _unknown_fiscal_period() -> FiscalPeriod:
    # MVP stub: real fiscal period should come from the filing's XBRL
    # context (contextRef -> period dates), not hardcoded. Wiring that up
    # requires threading XbrlFact.context_ref through to period lookup.
    today = date.today()
    return FiscalPeriod(
        fiscal_year=today.year,
        start_date=date(today.year, 1, 1),
        end_date=today,
        period_label=f"FY{today.year}",
    )
