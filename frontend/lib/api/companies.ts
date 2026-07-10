import { buildQuery, get } from './client'
import type { CompanySummaryResponse, FilingSummaryResponse } from './types'

export function searchCompanies(
  query: string,
  source: string = 'sec-edgar',
): Promise<CompanySummaryResponse[]> {
  return get(`/companies/search${buildQuery({ q: query, source })}`)
}

export function listFilings(
  identifier: string,
  source: string = 'sec-edgar',
): Promise<FilingSummaryResponse[]> {
  return get(`/companies/${encodeURIComponent(identifier)}/filings${buildQuery({ source })}`)
}
