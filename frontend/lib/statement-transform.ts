import type { FinancialStatementResponse, StatementCategory } from './api/types'
import type { SheetRow } from './types'

const CATEGORY_MAP: Record<StatementCategory, 'is' | 'bs' | 'cf'> = {
  income_statement: 'is',
  balance_sheet: 'bs',
  cash_flow: 'cf',
}

// With several companies, Apple's FY2026 and Microsoft's FY2026 must not share a column.
export function toColumnLabels(statements: FinancialStatementResponse[]): string[] {
  const multiCompany = new Set(statements.map((s) => s.company_name)).size > 1
  return statements.map((s) =>
    multiCompany ? `${s.company_name} ${s.period_label}` : s.period_label,
  )
}

export function toSheetRows(
  statements: FinancialStatementResponse[],
  category: StatementCategory,
): SheetRow[] {
  const rowsByField = new Map<string, SheetRow>()
  const columns = toColumnLabels(statements)

  for (const [index, statement] of statements.entries()) {
    const year = columns[index]
    for (const item of statement.line_items ?? []) {
      if (item.category !== category) continue
      let row = rowsByField.get(item.field_name)
      if (!row) {
        row = { label: item.field_name, xbrlTag: item.original_label }
        rowsByField.set(item.field_name, row)
      }
      // First value wins, like the exports: overlapping filings repeat a period.
      if (item.value !== null && row[year] === undefined) row[year] = item.value
    }
  }

  return Array.from(rowsByField.values())
}

export interface ExtractionResult {
  is: SheetRow[]
  bs: SheetRow[]
  cf: SheetRow[]
}

export function toExtractionResult(statements: FinancialStatementResponse[]): ExtractionResult {
  return {
    is: toSheetRows(statements, 'income_statement'),
    bs: toSheetRows(statements, 'balance_sheet'),
    cf: toSheetRows(statements, 'cash_flow'),
  }
}

export { CATEGORY_MAP }
