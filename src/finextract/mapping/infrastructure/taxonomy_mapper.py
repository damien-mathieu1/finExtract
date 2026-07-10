from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date

from finextract.extraction.domain.models import RawFiling, XbrlFact
from finextract.mapping.domain.models import FinancialStatement, LineItem
from finextract.shared_kernel.value_objects import (
    Currency,
    FiscalPeriod,
    ReportingStandard,
    StatementCategory,
)

logger = logging.getLogger(__name__)

_IS = StatementCategory.INCOME_STATEMENT
_BS = StatementCategory.BALANCE_SHEET
_CF = StatementCategory.CASH_FLOW

# Maps source taxonomy tags (company wording, via us-gaap/ifrs) to a standard
# schema field name + which statement it belongs to. Extend as new tags/
# wordings are encountered.
DEFAULT_TAG_MAP: dict[str, tuple[str, StatementCategory]] = {
    # Income statement
    "us-gaap:Revenues": ("revenue", _IS),
    "us-gaap:SalesRevenueNet": ("revenue", _IS),
    "us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax": ("revenue", _IS),
    "ifrs-full:Revenue": ("revenue", _IS),
    "us-gaap:CostOfRevenue": ("cost_of_revenue", _IS),
    "us-gaap:CostOfGoodsAndServicesSold": ("cost_of_revenue", _IS),
    "us-gaap:GrossProfit": ("gross_profit", _IS),
    "us-gaap:ResearchAndDevelopmentExpense": ("research_and_development", _IS),
    "us-gaap:SellingGeneralAndAdministrativeExpense": ("sga_expense", _IS),
    "us-gaap:OperatingExpenses": ("operating_expenses", _IS),
    "us-gaap:OperatingIncomeLoss": ("operating_income", _IS),
    "us-gaap:NonoperatingIncomeExpense": ("non_operating_income", _IS),
    "us-gaap:InterestExpense": ("interest_expense", _IS),
    "us-gaap:InvestmentIncomeInterest": ("interest_income", _IS),
    "us-gaap:IncomeLossFromContinuingOperationsBeforeIncomeTaxes": ("profit_before_tax", _IS),
    "us-gaap:IncomeTaxExpenseBenefit": ("income_tax_expense", _IS),
    "us-gaap:NetIncomeLoss": ("net_income", _IS),
    "ifrs-full:ProfitLoss": ("net_income", _IS),
    "us-gaap:EarningsPerShareBasic": ("eps_basic", _IS),
    "us-gaap:EarningsPerShareDiluted": ("eps_diluted", _IS),
    "us-gaap:WeightedAverageNumberOfSharesOutstandingBasic": ("shares_outstanding_basic", _IS),
    "us-gaap:WeightedAverageNumberOfDilutedSharesOutstanding": (
        "shares_outstanding_diluted",
        _IS,
    ),
    # Balance sheet
    "us-gaap:CashAndCashEquivalentsAtCarryingValue": ("cash_and_equivalents", _BS),
    "us-gaap:ShortTermInvestments": ("short_term_investments", _BS),
    "us-gaap:AccountsReceivableNetCurrent": ("accounts_receivable", _BS),
    "us-gaap:InventoryNet": ("inventory", _BS),
    "us-gaap:AssetsCurrent": ("total_current_assets", _BS),
    "us-gaap:PropertyPlantAndEquipmentNet": ("net_fixed_assets", _BS),
    "us-gaap:LongTermInvestments": ("long_term_investments", _BS),
    "us-gaap:Goodwill": ("goodwill", _BS),
    "us-gaap:IntangibleAssetsNetExcludingGoodwill": ("other_intangible_assets", _BS),
    "us-gaap:AssetsNoncurrent": ("total_non_current_assets", _BS),
    "us-gaap:Assets": ("total_assets", _BS),
    "us-gaap:AccountsPayableCurrent": ("accounts_payable", _BS),
    "us-gaap:ShortTermBorrowings": ("short_term_debt", _BS),
    "us-gaap:LiabilitiesCurrent": ("total_current_liabilities", _BS),
    "us-gaap:LongTermDebtNoncurrent": ("long_term_debt", _BS),
    "us-gaap:LiabilitiesNoncurrent": ("total_non_current_liabilities", _BS),
    "us-gaap:Liabilities": ("total_liabilities", _BS),
    "us-gaap:CommonStockValue": ("common_stock", _BS),
    "us-gaap:AdditionalPaidInCapital": ("additional_paid_in_capital", _BS),
    "us-gaap:RetainedEarningsAccumulatedDeficit": ("retained_earnings", _BS),
    "us-gaap:TreasuryStockValue": ("treasury_stock", _BS),
    "us-gaap:StockholdersEquity": ("total_equity", _BS),
    "us-gaap:LiabilitiesAndStockholdersEquity": ("total_liabilities_and_equity", _BS),
    # Cash flow statement
    "us-gaap:DepreciationDepletionAndAmortization": ("depreciation_and_amortization", _CF),
    "us-gaap:ShareBasedCompensation": ("stock_based_compensation", _CF),
    "us-gaap:NetCashProvidedByUsedInOperatingActivities": ("cash_flow_operating", _CF),
    "us-gaap:PaymentsToAcquirePropertyPlantAndEquipment": ("capex", _CF),
    "us-gaap:PaymentsToAcquireBusinessesNetOfCashAcquired": ("acquisitions", _CF),
    "us-gaap:NetCashProvidedByUsedInInvestingActivities": ("cash_flow_investing", _CF),
    "us-gaap:PaymentsOfDividends": ("dividends_paid", _CF),
    "us-gaap:ProceedsFromIssuanceOfCommonStock": ("proceeds_from_stock_issuance", _CF),
    "us-gaap:PaymentsForRepurchaseOfCommonStock": ("stock_buybacks", _CF),
    "us-gaap:NetCashProvidedByUsedInFinancingActivities": ("cash_flow_financing", _CF),
}

# EDINET (Japan) filers tag facts under the jp-gaap taxonomy (or jp-crp for
# some cover/company-info elements). Consolidated tags are used where a
# filer reports consolidated statements, which is the common case for the
# listed companies this adapter targets.
EDINET_TAG_MAP: dict[str, tuple[str, StatementCategory]] = {
    # Income statement
    "jp-gaap:NetSalesSummaryOfBusinessResults": ("revenue", _IS),
    "jp-gaap:OperatingRevenue1SummaryOfBusinessResults": ("revenue", _IS),
    "jp-gaap:CostOfSales": ("cost_of_revenue", _IS),
    "jp-gaap:GrossProfit": ("gross_profit", _IS),
    "jp-gaap:SellingGeneralAndAdministrativeExpenses": ("sga_expense", _IS),
    "jp-gaap:OperatingIncome": ("operating_income", _IS),
    "jp-gaap:OperatingIncomeSummaryOfBusinessResults": ("operating_income", _IS),
    "jp-gaap:NonOperatingIncome": ("non_operating_income", _IS),
    "jp-gaap:InterestExpense": ("interest_expense", _IS),
    "jp-gaap:InterestIncome": ("interest_income", _IS),
    "jp-gaap:IncomeBeforeIncomeTaxes": ("profit_before_tax", _IS),
    "jp-gaap:IncomeTaxesCurrentAndDeferred": ("income_tax_expense", _IS),
    "jp-gaap:ProfitLoss": ("net_income", _IS),
    "jp-gaap:NetIncomeSummaryOfBusinessResults": ("net_income", _IS),
    "jp-gaap:BasicEarningsPerShareSummaryOfBusinessResults": ("eps_basic", _IS),
    "jp-gaap:DilutedEarningsPerShareSummaryOfBusinessResults": ("eps_diluted", _IS),
    # Balance sheet
    "jp-gaap:CashAndDeposits": ("cash_and_equivalents", _BS),
    "jp-gaap:NotesAndAccountsReceivableTrade": ("accounts_receivable", _BS),
    "jp-gaap:Inventories": ("inventory", _BS),
    "jp-gaap:CurrentAssets": ("total_current_assets", _BS),
    "jp-gaap:PropertyPlantAndEquipment": ("net_fixed_assets", _BS),
    "jp-gaap:InvestmentsAndOtherAssets": ("long_term_investments", _BS),
    "jp-gaap:Goodwill": ("goodwill", _BS),
    "jp-gaap:NoncurrentAssets": ("total_non_current_assets", _BS),
    "jp-gaap:Assets": ("total_assets", _BS),
    "jp-gaap:AssetsSummaryOfBusinessResults": ("total_assets", _BS),
    "jp-gaap:NotesAndAccountsPayableTrade": ("accounts_payable", _BS),
    "jp-gaap:ShortTermLoansPayable": ("short_term_debt", _BS),
    "jp-gaap:CurrentLiabilities": ("total_current_liabilities", _BS),
    "jp-gaap:LongTermLoansPayable": ("long_term_debt", _BS),
    "jp-gaap:NoncurrentLiabilities": ("total_non_current_liabilities", _BS),
    "jp-gaap:Liabilities": ("total_liabilities", _BS),
    "jp-gaap:CapitalStock": ("common_stock", _BS),
    "jp-gaap:CapitalSurplus": ("additional_paid_in_capital", _BS),
    "jp-gaap:RetainedEarnings": ("retained_earnings", _BS),
    "jp-gaap:TreasuryStock": ("treasury_stock", _BS),
    "jp-gaap:NetAssetsSummaryOfBusinessResults": ("total_equity", _BS),
    "jp-gaap:LiabilitiesAndNetAssets": ("total_liabilities_and_equity", _BS),
    # Cash flow statement
    "jp-gaap:DepreciationAndAmortization": ("depreciation_and_amortization", _CF),
    "jp-gaap:NetCashProvidedByUsedInOperatingActivities": ("cash_flow_operating", _CF),
    "jp-gaap:PurchaseOfPropertyPlantAndEquipment": ("capex", _CF),
    "jp-gaap:PurchaseOfBusinessesNetOfCashAcquired": ("acquisitions", _CF),
    "jp-gaap:NetCashProvidedByUsedInInvestingActivities": ("cash_flow_investing", _CF),
    "jp-gaap:CashDividendsPaid": ("dividends_paid", _CF),
    "jp-gaap:ProceedsFromIssuanceOfCommonStock": ("proceeds_from_stock_issuance", _CF),
    "jp-gaap:PurchaseOfTreasuryStock": ("stock_buybacks", _CF),
    "jp-gaap:NetCashProvidedByUsedInFinancingActivities": ("cash_flow_financing", _CF),
}

_FULL_YEAR_MIN_DAYS = 350


@dataclass(slots=True)
class TagTableTaxonomyMapper:
    """TaxonomyMapperPort implementation backed by a static tag lookup table.

    Facts whose tag has no entry in the table are dropped from the standard
    schema but not lost: they stay retrievable from the RawFiling for
    auditing/debugging. A future adapter (e.g. LLM-assisted mapping for PDF
    extraction) implements the same port with fuzzier matching.
    """

    tag_map: dict[str, tuple[str, StatementCategory]] = field(
        default_factory=lambda: dict(DEFAULT_TAG_MAP)
    )
    currency: Currency = Currency.USD
    standard: ReportingStandard = ReportingStandard.US_GAAP

    def normalize(self, raw_filing: RawFiling) -> list[FinancialStatement]:
        by_period: dict[tuple[date, date], list[XbrlFact]] = defaultdict(list)
        dropped = 0
        for fact in raw_filing.facts:
            if fact.tag not in self.tag_map:
                continue
            if fact.period_start is None or fact.period_end is None:
                dropped += 1
                continue
            by_period[(fact.period_start, fact.period_end)].append(fact)

        if dropped:
            logger.warning(
                "Dropped %d fact(s) from %s: unresolved XBRL period (no matching context)",
                dropped,
                raw_filing.source_url,
            )

        statements = [
            FinancialStatement(
                company_name=raw_filing.company_name,
                fiscal_period=_fiscal_period_for(start, end),
                currency=self.currency,
                accounting_standard=self.standard,
                line_items=[
                    LineItem(
                        field_name=self.tag_map[fact.tag][0],
                        category=self.tag_map[fact.tag][1],
                        value=_to_float(fact),
                        original_label=fact.tag,
                        source="XBRL",
                    )
                    for fact in facts
                ],
            )
            for (start, end), facts in by_period.items()
        ]
        return sorted(statements, key=lambda s: s.fiscal_period.fiscal_year)


def _fiscal_period_for(start: date, end: date) -> FiscalPeriod:
    fiscal_year = end.year
    duration_days = (end - start).days
    if duration_days >= _FULL_YEAR_MIN_DAYS:
        period_label = f"FY{fiscal_year}"
    elif start == end:
        period_label = f"As of {end.isoformat()}"
    else:
        # Best-effort quarter guess from day-count - not calendar-aware,
        # just enough to distinguish quarterly from annual periods in labels.
        quarter = min(duration_days // 90 + 1, 4)
        period_label = f"Q{quarter} {fiscal_year}"
    return FiscalPeriod(
        fiscal_year=fiscal_year, start_date=start, end_date=end, period_label=period_label
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
