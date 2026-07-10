export type ExportFormat = 'csv' | 'excel' | 'json'

export interface CompanySummaryResponse {
  identifier: string
  name: string
  source: string
  ticker: string | null
}

export interface FilingSummaryResponse {
  accession_number: string
  form_type: string
  filing_date: string
  document_url: string
}

export type StatementCategory = 'income_statement' | 'balance_sheet' | 'cash_flow'

export interface LineItemResponse {
  field_name: string
  category: StatementCategory
  value: number | null
  original_label: string
  source: string
  page_number: number | null
  confidence_score: number | null
}

export interface FinancialStatementResponse {
  company_name: string
  fiscal_year: number
  period_label: string
  currency: string
  accounting_standard: string
  line_items: LineItemResponse[]
}

export interface ExtractionSummaryResponse {
  id: number
  company_name: string
  fiscal_year: number
  period_label: string
  currency: string
  accounting_standard: string
  source_reference: string
  extracted_at: string
  label: string | null
}
