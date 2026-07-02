import { buildQuery, get } from './client'
import type { CompanySummaryResponse, FilingSummaryResponse } from './types'

export function searchCompanies(query: string): Promise<CompanySummaryResponse[]> {
  return get(`/companies/search${buildQuery({ q: query })}`)
}

export function listFilings(cik: string): Promise<FilingSummaryResponse[]> {
  return get(`/companies/${encodeURIComponent(cik)}/filings`)
}
