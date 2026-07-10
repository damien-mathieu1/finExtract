import type { FinancialStatementResponse, StatementCategory } from './api/types'
import type { SheetRow } from './types'

const CATEGORY_MAP: Record<StatementCategory, 'is' | 'bs' | 'cf'> = {
  income_statement: 'is',
  balance_sheet: 'bs',
  cash_flow: 'cf',
}

export function toSheetRows(
  statements: FinancialStatementResponse[],
  category: StatementCategory,
): SheetRow[] {
  const rowsByField = new Map<string, SheetRow>()

  for (const statement of statements) {
    const year = statement.period_label
    for (const item of statement.line_items) {
      if (item.category !== category) continue
      let row = rowsByField.get(item.field_name)
      if (!row) {
        row = { label: item.field_name, xbrlTag: item.original_label }
        rowsByField.set(item.field_name, row)
      }
      if (item.value !== null) row[year] = item.value
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
