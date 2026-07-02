import { buildQuery, get, post } from './client'
import type { ExportFormat, ExtractionSummaryResponse, FinancialStatementResponse } from './types'

export function processFiling(
  documentUrl: string,
  format: ExportFormat = 'json',
): Promise<FinancialStatementResponse> {
  return post(`/filings/process${buildQuery({ document_url: documentUrl, format })}`)
}

export async function uploadFiling(
  file: File,
  format: ExportFormat = 'json',
): Promise<FinancialStatementResponse> {
  const form = new FormData()
  form.append('file', file)
  const res = await fetch(`/api/filings/upload${buildQuery({ format })}`, {
    method: 'POST',
    body: form,
  })
  if (!res.ok) {
    const detail = await res.json().catch(() => null)
    throw new Error(detail?.detail ?? res.statusText)
  }
  return res.json()
}

export function listExtractions(params: {
  companyIdentifier?: string
  sourceReference?: string
}): Promise<ExtractionSummaryResponse[]> {
  return get(
    `/extractions${buildQuery({
      company_identifier: params.companyIdentifier,
      source_reference: params.sourceReference,
    })}`,
  )
}

export function getExtraction(id: number): Promise<FinancialStatementResponse> {
  return get(`/extractions/${id}`)
}

export async function downloadExport(id: number, format: 'csv' | 'excel'): Promise<void> {
  const res = await fetch(`/api/extractions/${id}${buildQuery({ format })}`)
  if (!res.ok) throw new Error(`Export failed: ${res.status}`)

  const blob = await res.blob()
  const url = URL.createObjectURL(blob)
  const ext = format === 'csv' ? 'csv' : 'xlsx'
  const a = document.createElement('a')
  a.href = url
  a.download = `statement.${ext}`
  a.click()
  URL.revokeObjectURL(url)
}
