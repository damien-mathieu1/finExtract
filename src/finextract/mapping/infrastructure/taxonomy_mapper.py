from __future__ import annotations

import logging
from collections import Counter, defaultdict
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
# wordings are encountered. When a filing reports several tags for one field,
# the tag listed first wins, so order them by preference.
DEFAULT_TAG_MAP: dict[str, tuple[str, StatementCategory]] = {
    # Income statement
    "us-gaap:Revenues": ("revenue", _IS),
    "us-gaap:SalesRevenueNet": ("revenue", _IS),
    "us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax": ("revenue", _IS),
    "us-gaap:RevenueFromContractWithCustomerIncludingAssessedTax": ("revenue", _IS),
    "us-gaap:CostOfRevenue": ("cost_of_revenue", _IS),
    "us-gaap:CostOfGoodsAndServicesSold": ("cost_of_revenue", _IS),
    "us-gaap:CostOfGoodsSold": ("cost_of_revenue", _IS),
    "us-gaap:GrossProfit": ("gross_profit", _IS),
    "us-gaap:OtherOperatingIncomeExpenseNet": ("other_operating_income", _IS),
    "us-gaap:ResearchAndDevelopmentExpense": ("research_and_development", _IS),
    "us-gaap:SellingGeneralAndAdministrativeExpense": ("sga_expense", _IS),
    "us-gaap:OperatingExpenses": ("operating_expenses", _IS),
    "us-gaap:CostsAndExpenses": ("operating_expenses", _IS),
    "us-gaap:OperatingIncomeLoss": ("operating_income", _IS),
    "us-gaap:NonoperatingIncomeExpense": ("non_operating_income", _IS),
    "us-gaap:InterestExpense": ("interest_expense", _IS),
    "us-gaap:InvestmentIncomeInterest": ("interest_income", _IS),
    "us-gaap:ForeignCurrencyTransactionGainLossBeforeTax": ("fx_gain_loss", _IS),
    "us-gaap:OtherNonoperatingIncomeExpense": ("other_non_operating_income", _IS),
    "us-gaap:IncomeLossFromContinuingOperationsBeforeIncomeTaxes": ("profit_before_tax", _IS),
    "us-gaap:IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest": (  # noqa: E501
        "profit_before_tax",
        _IS,
    ),
    "us-gaap:IncomeLossFromContinuingOperationsBeforeIncomeTaxesMinorityInterestAndIncomeLossFromEquityMethodInvestments": (  # noqa: E501
        "profit_before_tax",
        _IS,
    ),
    "us-gaap:UnusualOrInfrequentItemNetGainLoss": ("abnormal_losses", _IS),
    "us-gaap:GoodwillAndIntangibleAssetImpairment": ("impairment_goodwill_intangibles", _IS),
    "us-gaap:LitigationSettlementExpense": ("litigation_settlement", _IS),
    "us-gaap:UnrealizedGainLossOnInvestments": ("unrealized_investment_gain_loss", _IS),
    "us-gaap:OtherNonrecurringIncomeExpense": ("other_one_time_items", _IS),
    "us-gaap:IncomeTaxExpenseBenefit": ("income_tax_expense", _IS),
    "us-gaap:CurrentIncomeTaxExpenseBenefit": ("current_income_tax", _IS),
    "us-gaap:DeferredIncomeTaxExpenseBenefit": ("deferred_income_tax", _IS),
    "us-gaap:IncomeLossFromContinuingOperations": ("income_from_continuing_operations", _IS),
    "us-gaap:ExtraordinaryItemNetOfTax": ("extraordinary_items_net_of_tax", _IS),
    "us-gaap:IncomeLossFromDiscontinuedOperationsNetOfTax": ("discontinued_operations", _IS),
    "us-gaap:CumulativeEffectOfNewAccountingPrincipleInPeriodOfAdoption": (
        "extraordinary_items_accounting_changes",
        _IS,
    ),
    "us-gaap:NetIncomeLossAttributableToNoncontrollingInterest": (
        "net_income_attributable_to_nci",
        _IS,
    ),
    "us-gaap:NetIncomeLoss": ("net_income", _IS),
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
    "us-gaap:AccountsAndNotesReceivableNet": ("accounts_and_notes_receivable", _BS),
    "us-gaap:AccountsReceivableNetCurrent": ("accounts_receivable", _BS),
    "us-gaap:NotesReceivableNet": ("notes_receivable", _BS),
    "us-gaap:InventoryNet": ("inventory", _BS),
    "us-gaap:InventoryRawMaterialsNetOfReserves": ("inventory_raw_materials", _BS),
    "us-gaap:InventoryWorkInProcessNetOfReserves": ("inventory_wip", _BS),
    "us-gaap:InventoryFinishedGoodsNetOfReserves": ("inventory_finished_goods", _BS),
    "us-gaap:OtherInventoryNetOfReserves": ("inventory_other", _BS),
    "us-gaap:OtherAssetsCurrent": ("other_current_assets", _BS),
    "us-gaap:PrepaidExpenseCurrent": ("prepaid_expenses_current", _BS),
    "us-gaap:DerivativeAssetsCurrent": ("derivative_assets_current", _BS),
    "us-gaap:DeferredTaxAssetsNetCurrent": ("deferred_tax_assets_current", _BS),
    "us-gaap:AssetsCurrent": ("total_current_assets", _BS),
    "us-gaap:PropertyPlantAndEquipmentNet": ("net_fixed_assets", _BS),
    "us-gaap:PropertyPlantAndEquipmentGross": ("gross_fixed_assets", _BS),
    "us-gaap:AccumulatedDepreciationDepletionAndAmortizationPropertyPlantAndEquipment": (
        "accumulated_depreciation",
        _BS,
    ),
    "us-gaap:LongTermInvestments": ("long_term_investments", _BS),
    "us-gaap:OtherAssetsNoncurrent": ("other_noncurrent_assets", _BS),
    "us-gaap:Goodwill": ("goodwill", _BS),
    "us-gaap:IntangibleAssetsNetExcludingGoodwill": ("other_intangible_assets", _BS),
    "us-gaap:PrepaidExpenseNoncurrent": ("prepaid_expenses_noncurrent", _BS),
    "us-gaap:DerivativeAssetsNoncurrent": ("derivative_assets_noncurrent", _BS),
    "us-gaap:AssetsNoncurrent": ("total_non_current_assets", _BS),
    "us-gaap:Assets": ("total_assets", _BS),
    "us-gaap:AccountsPayableAndAccruedLiabilitiesCurrent": (
        "accounts_payable_and_accrued",
        _BS,
    ),
    "us-gaap:AccountsPayableCurrent": ("accounts_payable", _BS),
    "us-gaap:AccruedIncomeTaxesCurrent": ("taxes_payable", _BS),
    "us-gaap:InterestAndDividendsPayableCurrentAndNoncurrent": (
        "interest_and_dividends_payable",
        _BS,
    ),
    "us-gaap:AccruedLiabilitiesCurrent": ("other_payables_and_accruals", _BS),
    "us-gaap:ShortTermBorrowings": ("short_term_debt", _BS),
    "us-gaap:DebtCurrent": ("short_term_debt", _BS),
    "us-gaap:FinanceLeaseLiabilityCurrent": ("finance_lease_liabilities_current", _BS),
    "us-gaap:OperatingLeaseLiabilityCurrent": ("operating_lease_liabilities_current", _BS),
    "us-gaap:LongTermDebtCurrent": ("current_portion_lt_debt", _BS),
    "us-gaap:OtherLiabilitiesCurrent": ("other_current_liabilities", _BS),
    "us-gaap:ContractWithCustomerLiabilityCurrent": ("deferred_revenue_current", _BS),
    "us-gaap:DerivativeLiabilitiesCurrent": ("derivative_liabilities_current", _BS),
    "us-gaap:LiabilitiesCurrent": ("total_current_liabilities", _BS),
    "us-gaap:LongTermDebtNoncurrent": ("long_term_debt", _BS),
    "us-gaap:FinanceLeaseLiabilityNoncurrent": ("finance_lease_liabilities_noncurrent", _BS),
    "us-gaap:OperatingLeaseLiabilityNoncurrent": ("operating_lease_liabilities_noncurrent", _BS),
    "us-gaap:OtherLiabilitiesNoncurrent": ("other_noncurrent_liabilities", _BS),
    "us-gaap:AccruedLiabilitiesNoncurrent": ("accrued_liabilities_noncurrent", _BS),
    "us-gaap:DefinedBenefitPensionPlanLiabilitiesNoncurrent": ("pension_liabilities", _BS),
    "us-gaap:LiabilityForOtherPostretirementBenefitsNoncurrent": (
        "other_postretirement_benefits",
        _BS,
    ),
    "us-gaap:ContractWithCustomerLiabilityNoncurrent": ("deferred_revenue_noncurrent", _BS),
    "us-gaap:DeferredTaxLiabilitiesNoncurrent": ("deferred_tax_liabilities_noncurrent", _BS),
    "us-gaap:DerivativeLiabilitiesNoncurrent": ("derivative_liabilities_noncurrent", _BS),
    "us-gaap:LiabilitiesNoncurrent": ("total_non_current_liabilities", _BS),
    "us-gaap:Liabilities": ("total_liabilities", _BS),
    "us-gaap:PreferredStockValue": ("preferred_stock", _BS),
    "us-gaap:CommonStockValue": ("common_stock", _BS),
    "us-gaap:AdditionalPaidInCapital": ("additional_paid_in_capital", _BS),
    "us-gaap:RetainedEarningsAccumulatedDeficit": ("retained_earnings", _BS),
    "us-gaap:TreasuryStockValue": ("treasury_stock", _BS),
    "us-gaap:MinorityInterest": ("noncontrolling_interest", _BS),
    # Including minorities first, so assets = liabilities + total_equity.
    "us-gaap:StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest": (
        "total_equity",
        _BS,
    ),
    "us-gaap:StockholdersEquity": ("total_equity", _BS),
    "us-gaap:LiabilitiesAndStockholdersEquity": ("total_liabilities_and_equity", _BS),
    # Cash flow statement
    "us-gaap:DepreciationDepletionAndAmortization": ("depreciation_and_amortization", _CF),
    "us-gaap:ShareBasedCompensation": ("stock_based_compensation", _CF),
    "us-gaap:OtherNoncashIncomeExpense": ("other_non_cash_adjustments", _CF),
    "us-gaap:IncreaseDecreaseInAccountsReceivable": ("change_in_accounts_receivable", _CF),
    "us-gaap:IncreaseDecreaseInInventories": ("change_in_inventories", _CF),
    "us-gaap:IncreaseDecreaseInAccountsPayable": ("change_in_accounts_payable", _CF),
    "us-gaap:IncreaseDecreaseInOtherOperatingCapitalNet": (
        "other_working_capital_changes",
        _CF,
    ),
    "us-gaap:CashProvidedByUsedInOperatingActivitiesDiscontinuedOperations": (
        "cash_flow_discontinued_operating",
        _CF,
    ),
    "us-gaap:NetCashProvidedByUsedInOperatingActivities": ("cash_flow_operating", _CF),
    "us-gaap:ProceedsFromSaleOfPropertyPlantAndEquipment": ("disposal_of_ppe", _CF),
    "us-gaap:PaymentsToAcquirePropertyPlantAndEquipment": ("capex", _CF),
    "us-gaap:PaymentsToAcquireIntangibleAssets": ("acquisition_of_intangible_assets", _CF),
    "us-gaap:ProceedsFromSaleMaturityAndCollectionsOfInvestments": (
        "proceeds_from_lt_investments",
        _CF,
    ),
    "us-gaap:PaymentsToAcquireInvestments": ("payments_for_lt_investments", _CF),
    "us-gaap:ProceedsFromDivestitureOfBusinessesNetOfCashDivested": (
        "proceeds_from_divestitures",
        _CF,
    ),
    "us-gaap:PaymentsToAcquireBusinessesNetOfCashAcquired": (
        "payments_for_acquisitions_subsidiaries",
        _CF,
    ),
    "us-gaap:PaymentsToAcquireInterestInJointVenture": (
        "payments_for_joint_ventures_associates",
        _CF,
    ),
    "us-gaap:PaymentsForProceedsFromOtherInvestingActivities": (
        "other_investing_activities",
        _CF,
    ),
    "us-gaap:CashProvidedByUsedInInvestingActivitiesDiscontinuedOperations": (
        "cash_flow_discontinued_investing",
        _CF,
    ),
    "us-gaap:NetCashProvidedByUsedInInvestingActivities": ("cash_flow_investing", _CF),
    "us-gaap:PaymentsOfDividends": ("dividends_paid", _CF),
    "us-gaap:ProceedsFromRepaymentsOfShortTermDebt": ("net_change_in_short_term_debt", _CF),
    "us-gaap:ProceedsFromIssuanceOfLongTermDebt": ("proceeds_from_lt_debt", _CF),
    "us-gaap:RepaymentsOfLongTermDebt": ("repayment_of_lt_debt", _CF),
    "us-gaap:ProceedsFromIssuanceOfCommonStock": ("proceeds_from_stock_issuance", _CF),
    "us-gaap:PaymentsForRepurchaseOfCommonStock": ("stock_buybacks", _CF),
    "us-gaap:ProceedsFromPaymentsForOtherFinancingActivities": (
        "other_financing_activities",
        _CF,
    ),
    "us-gaap:CashProvidedByUsedInFinancingActivitiesDiscontinuedOperations": (
        "cash_flow_discontinued_financing",
        _CF,
    ),
    "us-gaap:NetCashProvidedByUsedInFinancingActivities": ("cash_flow_financing", _CF),
    "us-gaap:EffectOfExchangeRateOnCashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents": (
        "fx_effect_on_cash",
        _CF,
    ),
    "us-gaap:CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalentsPeriodIncreaseDecreaseIncludingExchangeRateEffect": (  # noqa: E501
        "net_change_in_cash",
        _CF,
    ),
    "us-gaap:IncomeTaxesPaidNet": ("income_taxes_paid", _CF),
    "us-gaap:InterestPaidNet": ("interest_paid", _CF),
    # IFRS (ifrs-full), for 20-F and uploaded filers. Filer extension tags stay
    # unmapped (Toyota's capex is tm:..., for example).
    "ifrs-full:Revenue": ("revenue", _IS),
    "ifrs-full:CostOfSales": ("cost_of_revenue", _IS),
    "ifrs-full:GrossProfit": ("gross_profit", _IS),
    "ifrs-full:OtherIncome": ("other_operating_income", _IS),
    "ifrs-full:ResearchAndDevelopmentExpense": ("research_and_development", _IS),
    "ifrs-full:SellingGeneralAndAdministrativeExpense": ("sga_expense", _IS),
    "ifrs-full:OperatingExpense": ("operating_expenses", _IS),
    "ifrs-full:ProfitLossFromOperatingActivities": ("operating_income", _IS),
    "ifrs-full:InterestExpense": ("interest_expense", _IS),
    "ifrs-full:FinanceCosts": ("interest_expense", _IS),
    "ifrs-full:InterestRevenueCalculatedUsingEffectiveInterestMethod": ("interest_income", _IS),
    "ifrs-full:GainsLossesOnExchangeDifferencesOnTranslationRecognisedInProfitOrLoss": (
        "fx_gain_loss",
        _IS,
    ),
    "ifrs-full:ProfitLossBeforeTax": ("profit_before_tax", _IS),
    "ifrs-full:IncomeTaxExpenseContinuingOperations": ("income_tax_expense", _IS),
    "ifrs-full:CurrentTaxExpenseIncome": ("current_income_tax", _IS),
    "ifrs-full:DeferredTaxExpenseIncome": ("deferred_income_tax", _IS),
    "ifrs-full:DeferredTaxExpenseIncomeRecognisedInProfitOrLoss": ("deferred_income_tax", _IS),
    "ifrs-full:ProfitLossFromContinuingOperations": ("income_from_continuing_operations", _IS),
    "ifrs-full:ProfitLossFromDiscontinuedOperations": ("discontinued_operations", _IS),
    # Attributable to the parent first, matching us-gaap:NetIncomeLoss.
    "ifrs-full:ProfitLossAttributableToOwnersOfParent": ("net_income", _IS),
    "ifrs-full:ProfitLoss": ("net_income", _IS),
    "ifrs-full:ProfitLossAttributableToNoncontrollingInterests": (
        "net_income_attributable_to_nci",
        _IS,
    ),
    "ifrs-full:BasicEarningsLossPerShare": ("eps_basic", _IS),
    "ifrs-full:DilutedEarningsLossPerShare": ("eps_diluted", _IS),
    "ifrs-full:WeightedAverageShares": ("shares_outstanding_basic", _IS),
    "ifrs-full:AdjustedWeightedAverageShares": ("shares_outstanding_diluted", _IS),
    "ifrs-full:CashAndCashEquivalents": ("cash_and_equivalents", _BS),
    "ifrs-full:CurrentInvestments": ("short_term_investments", _BS),
    "ifrs-full:TradeAndOtherCurrentReceivables": ("accounts_and_notes_receivable", _BS),
    "ifrs-full:CurrentTradeReceivables": ("accounts_receivable", _BS),
    "ifrs-full:Inventories": ("inventory", _BS),
    "ifrs-full:RawMaterials": ("inventory_raw_materials", _BS),
    "ifrs-full:WorkInProgress": ("inventory_wip", _BS),
    "ifrs-full:FinishedGoods": ("inventory_finished_goods", _BS),
    "ifrs-full:OtherCurrentAssets": ("other_current_assets", _BS),
    "ifrs-full:CurrentPrepaidExpenses": ("prepaid_expenses_current", _BS),
    "ifrs-full:CurrentAssets": ("total_current_assets", _BS),
    "ifrs-full:PropertyPlantAndEquipment": ("net_fixed_assets", _BS),
    "ifrs-full:Goodwill": ("goodwill", _BS),
    "ifrs-full:IntangibleAssetsOtherThanGoodwill": ("other_intangible_assets", _BS),
    "ifrs-full:IntangibleAssetsAndGoodwill": ("total_intangibles", _BS),
    "ifrs-full:DeferredTaxAssets": ("deferred_tax_assets", _BS),
    "ifrs-full:OtherNoncurrentAssets": ("other_noncurrent_assets", _BS),
    "ifrs-full:NoncurrentAssets": ("total_noncurrent_assets", _BS),
    "ifrs-full:Assets": ("total_assets", _BS),
    "ifrs-full:TradeAndOtherCurrentPayables": ("accounts_payable_and_accrued", _BS),
    "ifrs-full:TradeAndOtherCurrentPayablesToTradeSuppliers": ("accounts_payable", _BS),
    "ifrs-full:CurrentTaxLiabilitiesCurrent": ("taxes_payable", _BS),
    "ifrs-full:CurrentBorrowingsAndCurrentPortionOfNoncurrentBorrowings": (
        "short_term_debt",
        _BS,
    ),
    "ifrs-full:ShorttermBorrowings": ("short_term_debt", _BS),
    "ifrs-full:CurrentPortionOfLongtermBorrowings": ("current_portion_lt_debt", _BS),
    "ifrs-full:CurrentLeaseLiabilities": ("lease_liabilities_current", _BS),
    "ifrs-full:CurrentContractLiabilities": ("deferred_revenue_current", _BS),
    "ifrs-full:OtherCurrentLiabilities": ("other_current_liabilities", _BS),
    "ifrs-full:CurrentLiabilities": ("total_current_liabilities", _BS),
    "ifrs-full:LongtermBorrowings": ("long_term_debt", _BS),
    "ifrs-full:NoncurrentPortionOfNoncurrentBorrowings": ("long_term_debt", _BS),
    "ifrs-full:NoncurrentLeaseLiabilities": ("lease_liabilities_noncurrent", _BS),
    "ifrs-full:NoncurrentRecognisedLiabilitiesDefinedBenefitPlan": ("pension_liabilities", _BS),
    "ifrs-full:DeferredTaxLiabilities": ("deferred_tax_liabilities_noncurrent", _BS),
    "ifrs-full:OtherNoncurrentLiabilities": ("other_noncurrent_liabilities", _BS),
    "ifrs-full:NoncurrentLiabilities": ("total_noncurrent_liabilities", _BS),
    "ifrs-full:Liabilities": ("total_liabilities", _BS),
    "ifrs-full:IssuedCapital": ("common_stock", _BS),
    "ifrs-full:AdditionalPaidinCapital": ("additional_paid_in_capital", _BS),
    "ifrs-full:SharePremium": ("additional_paid_in_capital", _BS),
    "ifrs-full:TreasuryShares": ("treasury_stock", _BS),
    "ifrs-full:RetainedEarnings": ("retained_earnings", _BS),
    "ifrs-full:OtherReserves": ("other_equity", _BS),
    "ifrs-full:EquityAttributableToOwnersOfParent": ("equity_attributable_to_parent", _BS),
    "ifrs-full:NoncontrollingInterests": ("noncontrolling_interest", _BS),
    "ifrs-full:Equity": ("total_equity", _BS),
    "ifrs-full:EquityAndLiabilities": ("total_liabilities_and_equity", _BS),
    "ifrs-full:AdjustmentsForDepreciationAndAmortisationExpense": (
        "depreciation_and_amortization",
        _CF,
    ),
    "ifrs-full:DepreciationAndAmortisationExpense": ("depreciation_and_amortization", _CF),
    "ifrs-full:AdjustmentsForSharebasedPayments": ("stock_based_compensation", _CF),
    # Cash-impact sign, unlike the us-gaap IncreaseDecreaseIn* tags.
    "ifrs-full:AdjustmentsForDecreaseIncreaseInTradeAndOtherReceivables": (
        "change_in_accounts_receivable",
        _CF,
    ),
    "ifrs-full:AdjustmentsForDecreaseIncreaseInInventories": ("change_in_inventories", _CF),
    "ifrs-full:AdjustmentsForIncreaseDecreaseInTradeAndOtherPayables": (
        "change_in_accounts_payable",
        _CF,
    ),
    "ifrs-full:CashFlowsFromUsedInOperatingActivities": ("cash_flow_operating", _CF),
    "ifrs-full:PurchaseOfPropertyPlantAndEquipmentClassifiedAsInvestingActivities": ("capex", _CF),
    "ifrs-full:ProceedsFromSalesOfPropertyPlantAndEquipmentClassifiedAsInvestingActivities": (
        "disposal_of_ppe",
        _CF,
    ),
    "ifrs-full:PurchaseOfIntangibleAssetsClassifiedAsInvestingActivities": (
        "acquisition_of_intangible_assets",
        _CF,
    ),
    "ifrs-full:CashFlowsUsedInObtainingControlOfSubsidiariesOrOtherBusinessesClassifiedAsInvestingActivities": (  # noqa: E501
        "payments_for_acquisitions_subsidiaries",
        _CF,
    ),
    "ifrs-full:OtherInflowsOutflowsOfCashClassifiedAsInvestingActivities": (
        "other_investing_activities",
        _CF,
    ),
    "ifrs-full:CashFlowsFromUsedInInvestingActivities": ("cash_flow_investing", _CF),
    "ifrs-full:DividendsPaidClassifiedAsFinancingActivities": ("dividends_paid", _CF),
    "ifrs-full:DividendsPaidToEquityHoldersOfParentClassifiedAsFinancingActivities": (
        "dividends_paid",
        _CF,
    ),
    "ifrs-full:CashFlowsFromUsedInIncreaseDecreaseInCurrentBorrowings": (
        "net_change_in_short_term_debt",
        _CF,
    ),
    "ifrs-full:ProceedsFromNoncurrentBorrowings": ("proceeds_from_lt_debt", _CF),
    "ifrs-full:ProceedsFromBorrowingsClassifiedAsFinancingActivities": (
        "proceeds_from_lt_debt",
        _CF,
    ),
    "ifrs-full:RepaymentsOfNoncurrentBorrowings": ("repayment_of_lt_debt", _CF),
    "ifrs-full:RepaymentsOfBorrowingsClassifiedAsFinancingActivities": (
        "repayment_of_lt_debt",
        _CF,
    ),
    "ifrs-full:ProceedsFromIssuingShares": ("proceeds_from_stock_issuance", _CF),
    "ifrs-full:PaymentsToAcquireOrRedeemEntitysShares": ("stock_buybacks", _CF),
    "ifrs-full:OtherInflowsOutflowsOfCashClassifiedAsFinancingActivities": (
        "other_financing_activities",
        _CF,
    ),
    "ifrs-full:CashFlowsFromUsedInFinancingActivities": ("cash_flow_financing", _CF),
    "ifrs-full:EffectOfExchangeRateChangesOnCashAndCashEquivalents": ("fx_effect_on_cash", _CF),
    "ifrs-full:IncreaseDecreaseInCashAndCashEquivalents": ("net_change_in_cash", _CF),
    "ifrs-full:IncomeTaxesPaidRefundClassifiedAsOperatingActivities": ("income_taxes_paid", _CF),
    "ifrs-full:InterestPaidClassifiedAsOperatingActivities": ("interest_paid", _CF),
}

# EDINET (Japan) filers tag standard consolidated financial statement facts
# under the jppfs_cor namespace (J-GAAP), the 5-year cover-page summary
# under jpcrp_cor, and (for the many large-cap filers reporting under IFRS,
# e.g. Toyota) core P&L/BS facts under jpigp_cor. Revenue under IFRS is
# frequently tagged with a company-specific extension element rather than a
# stable jpigp_cor tag (EDINET's IFRS revenue taxonomy is filer-extensible),
# so it isn't reliably mappable here the way jppfs_cor:NetSales is for
# J-GAAP filers.
EDINET_TAG_MAP: dict[str, tuple[str, StatementCategory]] = {
    # Income statement (J-GAAP)
    "jppfs_cor:NetSales": ("revenue", _IS),
    "jppfs_cor:CostOfSales": ("cost_of_revenue", _IS),
    "jppfs_cor:GrossProfit": ("gross_profit", _IS),
    "jppfs_cor:SellingGeneralAndAdministrativeExpenses": ("sga_expense", _IS),
    "jppfs_cor:OperatingIncome": ("operating_income", _IS),
    "jppfs_cor:NonOperatingIncome": ("non_operating_income", _IS),
    "jppfs_cor:InterestExpense": ("interest_expense", _IS),
    "jppfs_cor:InterestIncome": ("interest_income", _IS),
    "jppfs_cor:ForeignExchangeGainsLosses": ("fx_gain_loss", _IS),
    "jppfs_cor:OtherNonOperatingIncome": ("other_non_operating_income", _IS),
    "jppfs_cor:IncomeBeforeIncomeTaxes": ("profit_before_tax", _IS),
    "jppfs_cor:ImpairmentLoss": ("impairment_goodwill_intangibles", _IS),
    "jppfs_cor:IncomeTaxesCurrentAndDeferred": ("income_tax_expense", _IS),
    "jppfs_cor:IncomeTaxesCurrent": ("current_income_tax", _IS),
    "jppfs_cor:IncomeTaxesDeferred": ("deferred_income_tax", _IS),
    "jppfs_cor:ProfitLossFromDiscontinuedOperations": ("discontinued_operations", _IS),
    "jppfs_cor:ProfitLossAttributableToNonControllingInterests": (
        "net_income_attributable_to_nci",
        _IS,
    ),
    "jppfs_cor:ProfitLoss": ("net_income", _IS),
    "jppfs_cor:BasicEarningsPerShare": ("eps_basic", _IS),
    "jppfs_cor:DilutedEarningsPerShare": ("eps_diluted", _IS),
    # Income statement (IFRS, e.g. Toyota/Sony-style filers)
    "jpigp_cor:OperatingProfitLossIFRS": ("operating_income", _IS),
    "jpigp_cor:ProfitLossBeforeTaxIFRS": ("profit_before_tax", _IS),
    "jpigp_cor:ProfitLossIFRS": ("net_income", _IS),
    "jpigp_cor:ProfitLossAttributableToOwnersOfParentIFRS": ("net_income", _IS),
    # Balance sheet (J-GAAP)
    "jppfs_cor:CashAndDeposits": ("cash_and_equivalents", _BS),
    "jppfs_cor:NotesAndAccountsReceivableTrade": ("accounts_receivable", _BS),
    "jppfs_cor:Inventories": ("inventory", _BS),
    "jppfs_cor:CurrentAssets": ("total_current_assets", _BS),
    "jppfs_cor:PropertyPlantAndEquipment": ("net_fixed_assets", _BS),
    "jppfs_cor:InvestmentsAndOtherAssets": ("long_term_investments", _BS),
    "jppfs_cor:Goodwill": ("goodwill", _BS),
    "jppfs_cor:NoncurrentAssets": ("total_non_current_assets", _BS),
    "jppfs_cor:Assets": ("total_assets", _BS),
    "jppfs_cor:NotesAndAccountsPayableTrade": ("accounts_payable", _BS),
    "jppfs_cor:ShortTermLoansPayable": ("short_term_debt", _BS),
    "jppfs_cor:CurrentLiabilities": ("total_current_liabilities", _BS),
    "jppfs_cor:LongTermLoansPayable": ("long_term_debt", _BS),
    "jppfs_cor:NoncurrentLiabilities": ("total_non_current_liabilities", _BS),
    "jppfs_cor:Liabilities": ("total_liabilities", _BS),
    "jppfs_cor:CapitalStock": ("common_stock", _BS),
    "jppfs_cor:CapitalSurplus": ("additional_paid_in_capital", _BS),
    "jppfs_cor:RetainedEarnings": ("retained_earnings", _BS),
    "jppfs_cor:TreasuryStock": ("treasury_stock", _BS),
    "jppfs_cor:NonControllingInterests": ("noncontrolling_interest", _BS),
    "jppfs_cor:NetAssets": ("total_equity", _BS),
    "jppfs_cor:LiabilitiesAndNetAssets": ("total_liabilities_and_equity", _BS),
    # Balance sheet (IFRS)
    "jpigp_cor:AssetsIFRS": ("total_assets", _BS),
    "jpigp_cor:CurrentAssetsIFRS": ("total_current_assets", _BS),
    "jpigp_cor:NonCurrentAssetsIFRS": ("total_non_current_assets", _BS),
    "jpigp_cor:IntangibleAssetsIFRS": ("other_intangible_assets", _BS),
    "jpigp_cor:DeferredTaxAssetsIFRS": ("deferred_tax_assets", _BS),
    # Cash flow statement (J-GAAP)
    "jppfs_cor:DepreciationAndAmortization": ("depreciation_and_amortization", _CF),
    "jppfs_cor:NetCashProvidedByUsedInOperatingActivities": ("cash_flow_operating", _CF),
    "jppfs_cor:PurchaseOfPropertyPlantAndEquipment": ("capex", _CF),
    "jppfs_cor:ProceedsFromSaleOfPropertyPlantAndEquipment": ("disposal_of_ppe", _CF),
    "jppfs_cor:PurchaseOfIntangibleAssets": ("acquisition_of_intangible_assets", _CF),
    "jppfs_cor:PurchaseOfInvestmentSecurities": ("payments_for_lt_investments", _CF),
    "jppfs_cor:ProceedsFromSaleOfInvestmentSecurities": ("proceeds_from_lt_investments", _CF),
    "jppfs_cor:PurchaseOfBusinessesNetOfCashAcquired": (
        "payments_for_acquisitions_subsidiaries",
        _CF,
    ),
    "jppfs_cor:NetCashProvidedByUsedInInvestingActivities": ("cash_flow_investing", _CF),
    "jppfs_cor:CashDividendsPaid": ("dividends_paid", _CF),
    "jppfs_cor:ProceedsFromIssuanceOfCommonStock": ("proceeds_from_stock_issuance", _CF),
    "jppfs_cor:PurchaseOfTreasuryStock": ("stock_buybacks", _CF),
    "jppfs_cor:NetCashProvidedByUsedInFinancingActivities": ("cash_flow_financing", _CF),
    "jppfs_cor:EffectOfExchangeRateChangeOnCashAndCashEquivalents": (
        "fx_effect_on_cash",
        _CF,
    ),
    "jppfs_cor:NetIncreaseDecreaseInCashAndCashEquivalents": ("net_change_in_cash", _CF),
}

_FULL_YEAR_MIN_DAYS = 350
_DAYS_PER_MONTH = 30.44

_STANDARD_BY_TAG_PREFIX = {
    "us-gaap": ReportingStandard.US_GAAP,
    "ifrs-full": ReportingStandard.IFRS,
    "jpigp_cor": ReportingStandard.IFRS,
    "jppfs_cor": ReportingStandard.JAPANESE_GAAP,
}


@dataclass(slots=True)
class TagTableTaxonomyMapper:
    """TaxonomyMapperPort implementation backed by a static tag lookup table.

    Facts whose tag has no entry in the table are dropped from the standard
    schema but not lost: they stay retrievable from the RawFiling for
    auditing/debugging. A future adapter (e.g. LLM-assisted mapping for PDF
    extraction) implements the same port with fuzzier matching.

    `currency` and `standard` are fallbacks: both are read from the filing's
    own facts whenever those say.
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
            logger.info(
                "Dropped %d fact(s) from %s: dimensional or unresolved XBRL context",
                dropped,
                raw_filing.source_url,
            )

        kept_facts = [fact for facts in by_period.values() for fact in facts]
        currency = _filing_currency(kept_facts) or self.currency
        standard = _filing_standard(kept_facts) or self.standard

        statements = [
            FinancialStatement(
                company_name=raw_filing.company_name,
                fiscal_period=_fiscal_period_for(start, end),
                currency=currency,
                accounting_standard=standard,
                line_items=[
                    LineItem(
                        field_name=self.tag_map[fact.tag][0],
                        category=self.tag_map[fact.tag][1],
                        value=_to_float(fact),
                        original_label=fact.tag,
                        source="XBRL",
                    )
                    for fact in _one_fact_per_field(facts, self.tag_map)
                ],
            )
            for (start, end), facts in by_period.items()
        ]
        return sorted(statements, key=lambda s: s.fiscal_period.fiscal_year)


def _filing_currency(facts: list[XbrlFact]) -> Currency | None:
    codes = Counter(fact.currency for fact in facts if fact.currency)
    if not codes:
        return None
    try:
        return Currency(codes.most_common(1)[0][0])
    except ValueError:
        return Currency.UNKNOWN


def _filing_standard(facts: list[XbrlFact]) -> ReportingStandard | None:
    standards = Counter(
        _STANDARD_BY_TAG_PREFIX[prefix]
        for prefix in (fact.tag.partition(":")[0] for fact in facts)
        if prefix in _STANDARD_BY_TAG_PREFIX
    )
    return standards.most_common(1)[0][0] if standards else None


def _one_fact_per_field(
    facts: list[XbrlFact], tag_map: dict[str, tuple[str, StatementCategory]]
) -> list[XbrlFact]:
    """A filing repeats a figure across statements and notes, sometimes rounded
    or under a sibling tag. Keep one per field, in filing order: a real value,
    then the preferred tag, then the most precise. No decimals means exact."""
    tag_rank = {tag: rank for rank, tag in enumerate(tag_map)}

    def preference(fact: XbrlFact) -> tuple[bool, int, float]:
        decimals = float("inf") if fact.decimals is None else fact.decimals
        return (_to_float(fact) is None, tag_rank[fact.tag], -decimals)

    best: dict[tuple[str, StatementCategory], XbrlFact] = {}
    for fact in sorted(facts, key=preference):
        best.setdefault(tag_map[fact.tag], fact)
    return [fact for fact in facts if best[tag_map[fact.tag]] is fact]


def _fiscal_year_for(end: date) -> int:
    # 52/53-week years ending nearest Dec 31 can spill into January: J&J's
    # fiscal 2022 ended 2023-01-01 and must not collide with fiscal 2023.
    return end.year - 1 if end.month == 1 and end.day <= 7 else end.year


def _fiscal_period_for(start: date, end: date) -> FiscalPeriod:
    fiscal_year = _fiscal_year_for(end)
    duration_days = (end - start).days
    if duration_days >= _FULL_YEAR_MIN_DAYS:
        period_label = f"FY{fiscal_year}"
    elif start == end:
        period_label = f"As of {end.isoformat()}"
    else:
        # Length and end date, not "Q2": a quarter number needs the filer's
        # fiscal calendar, and 10-Qs mix 3-month and year-to-date periods.
        months = round(duration_days / _DAYS_PER_MONTH)
        period_label = f"{months}M to {end.isoformat()}"
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
