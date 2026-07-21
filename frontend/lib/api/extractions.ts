import { authHeaders, buildQuery, get, post } from './client'
import type { ExportFormat, ExtractionSummaryResponse, FinancialStatementResponse } from './types'

export function processFiling(
  documentUrl: string,
  cik?: string,
  ticker?: string | null,
  format: ExportFormat = 'json',
  label?: string,
  source: string = 'sec-edgar',
): Promise<FinancialStatementResponse[]> {
  return post(
    `/filings/process${buildQuery({
      document_url: documentUrl,
      source,
      cik,
      ticker: ticker ?? undefined,
      format,
      label,
    })}`,
  )
}

export async function uploadFiling(
  file: File,
  format: ExportFormat = 'json',
  label?: string,
): Promise<FinancialStatementResponse[]> {
  const form = new FormData()
  form.append('file', file)
  const res = await fetch(`/api/filings/upload${buildQuery({ format, label })}`, {
    method: 'POST',
    body: form,
    // Authorization only: Content-Type must stay unset so the browser
    // generates the multipart boundary.
    headers: await authHeaders(),
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

function combineQuery(ids: number[], format: string): string {
  const search = new URLSearchParams()
  ids.forEach((id) => search.append('ids', String(id)))
  search.set('format', format)
  return `?${search.toString()}`
}

function combineByCompanyQuery(
  params: { cik?: string; companyName?: string },
  format: string,
): string {
  return buildQuery({ cik: params.cik, company_name: params.companyName, format })
}

export function combineExtractions(ids: number[]): Promise<FinancialStatementResponse[]> {
  return get(`/extractions/combine${combineQuery(ids, 'json')}`)
}

export function combineByCompany(params: {
  cik?: string
  companyName?: string
}): Promise<FinancialStatementResponse[]> {
  return get(`/extractions/combine${combineByCompanyQuery(params, 'json')}`)
}

export async function downloadExport(id: number, format: 'csv' | 'excel'): Promise<void> {
  const res = await fetch(`/api/extractions/${id}${buildQuery({ format })}`, {
    headers: await authHeaders(),
  })
  if (!res.ok) throw new Error(`Export failed: ${res.status}`)
  await triggerDownload(res, format)
}

export async function downloadCombinedExport(
  ids: number[],
  format: 'csv' | 'excel',
): Promise<void> {
  const res = await fetch(`/api/extractions/combine${combineQuery(ids, format)}`, {
    headers: await authHeaders(),
  })
  if (!res.ok) throw new Error(`Export failed: ${res.status}`)
  await triggerDownload(res, format)
}

export async function downloadCombinedByCompanyExport(
  params: { cik?: string; companyName?: string },
  format: 'csv' | 'excel',
): Promise<void> {
  const res = await fetch(`/api/extractions/combine${combineByCompanyQuery(params, format)}`, {
    headers: await authHeaders(),
  })
  if (!res.ok) throw new Error(`Export failed: ${res.status}`)
  await triggerDownload(res, format)
}

async function triggerDownload(res: Response, format: 'csv' | 'excel'): Promise<void> {
  const blob = await res.blob()
  const url = URL.createObjectURL(blob)
  const ext = format === 'csv' ? 'csv' : 'xlsx'
  const a = document.createElement('a')
  a.href = url
  a.download = `statement.${ext}`
  a.click()
  URL.revokeObjectURL(url)
}
