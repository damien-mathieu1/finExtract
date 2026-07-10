'use client'

import { useState, useRef } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Search,
  Upload,
  AlertTriangle,
  CheckCircle2,
  Loader2,
  X,
  ArrowLeft,
  Plus,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import { useTranslation } from '@/lib/i18n'
import { searchCompanies, listFilings } from '@/lib/api/companies'
import { processFiling, uploadFiling } from '@/lib/api/extractions'
import type { CompanySummaryResponse, FilingSummaryResponse } from '@/lib/api/types'
import type { FilingSource } from '@/lib/types'
import { toast } from 'sonner'
import type { AppPage } from '@/components/app-sidebar'

const SOURCE_TABS: { id: FilingSource; supported: boolean }[] = [
  { id: 'sec-edgar', supported: true },
  { id: 'edinet', supported: true },
  { id: 'xbrl-api', supported: false },
  { id: 'upload-xbrl', supported: true },
  { id: 'upload-pdf', supported: false },
]

const DIRECTORY_SOURCES: FilingSource[] = ['sec-edgar', 'edinet']
const DEFAULT_LOOKBACK_DAYS = 120
const LOOKBACK_STEP_DAYS = 365

interface FilingSearchProps {
  onNavigate: (page: AppPage) => void
}

export function FilingSearchPage({ onNavigate }: FilingSearchProps) {
  const { t } = useTranslation()
  const queryClient = useQueryClient()

  const [sourceTab, setSourceTab] = useState<FilingSource>('sec-edgar')
  const [query, setQuery] = useState('')
  const [searchedQuery, setSearchedQuery] = useState<string | null>(null)
  const [selectedCompany, setSelectedCompany] = useState<CompanySummaryResponse | null>(null)
  const [selectedFiling, setSelectedFiling] = useState<FilingSummaryResponse | null>(null)
  const [uploadedFile, setUploadedFile] = useState<File | null>(null)
  const [label, setLabel] = useState('')
  const fileRef = useRef<HTMLInputElement>(null)
  // Mobile: track which "step" is shown (0 = search/results, 1 = extract)
  const [mobileStep, setMobileStep] = useState<0 | 1>(0)

  const isDirectorySource = DIRECTORY_SOURCES.includes(sourceTab)
  const [lookbackDays, setLookbackDays] = useState(DEFAULT_LOOKBACK_DAYS)

  const companiesQuery = useQuery({
    queryKey: ['companies', sourceTab, searchedQuery],
    queryFn: () => searchCompanies(searchedQuery ?? '', sourceTab),
    enabled: isDirectorySource && !!searchedQuery,
  })

  const filingsQuery = useQuery({
    queryKey: ['filings', sourceTab, selectedCompany?.identifier, lookbackDays],
    queryFn: () => listFilings(selectedCompany!.identifier, sourceTab, lookbackDays),
    enabled: isDirectorySource && !!selectedCompany,
  })

  const extractMutation = useMutation({
    mutationFn: async () => {
      if (sourceTab === 'upload-xbrl' && uploadedFile) {
        return uploadFiling(uploadedFile, 'json', label.trim() || undefined)
      }
      if (selectedFiling && selectedCompany) {
        return processFiling(
          selectedFiling.document_url,
          selectedCompany.identifier,
          selectedCompany.ticker,
          'json',
          label.trim() || undefined,
          sourceTab
        )
      }
      throw new Error(t('filingSearch.toasts.nothingSelected'))
    },
    onSuccess: async (statements) => {
      await queryClient.invalidateQueries({ queryKey: ['extractions'] })
      toast.success(t('filingSearch.toasts.extractionCompleted', { count: statements.length }), {
        action: {
          label: t('filingSearch.toasts.viewAction'),
          onClick: () => onNavigate('extractions'),
        },
      })
      setSelectedFiling(null)
      setUploadedFile(null)
      setMobileStep(0)
    },
    onError: (error) => {
      toast.error(error instanceof Error ? error.message : t('filingSearch.toasts.extractionFailed'))
    },
  })

  function handleSearch() {
    if (!query.trim()) return
    setSelectedCompany(null)
    setSelectedFiling(null)
    setSearchedQuery(query.trim())
  }

  function handleSelectCompany(company: CompanySummaryResponse) {
    setSelectedCompany(company)
    setSelectedFiling(null)
    setLookbackDays(DEFAULT_LOOKBACK_DAYS)
  }

  function handleSelectFiling(filing: FilingSummaryResponse) {
    setSelectedFiling(filing)
    setLabel(
      `${selectedCompany?.ticker ?? selectedCompany?.name ?? ''} ${filing.form_type} - filed ${filing.filing_date}`.trim()
    )
    setMobileStep(1)
  }

  function handleBackToSearch() {
    setSelectedFiling(null)
    setMobileStep(0)
  }

  const isSearching = companiesQuery.isFetching
  const companies = companiesQuery.data ?? []
  const filings = filingsQuery.data ?? []
  const idLabel =
    sourceTab === 'sec-edgar' || sourceTab === 'edinet'
      ? t(`filingSearch.idLabel.${sourceTab}`)
      : ''

  // ─── Search/Results panel ───────────────────────────────────────────────────
  const SearchPanel = (
    <div
      className={cn(
        'flex flex-col min-h-0',
        'md:w-[400px] md:shrink-0 md:border-r md:border-border md:overflow-y-auto',
        mobileStep === 1 ? 'hidden md:flex' : 'flex flex-1 overflow-y-auto'
      )}
    >
      <div className="p-4 md:p-6 border-b border-border shrink-0">
        <h1 className="text-lg md:text-xl font-semibold text-foreground">
          {t('filingSearch.title')}
        </h1>
        <p className="text-sm text-muted-foreground mt-0.5">{t('filingSearch.subtitle')}</p>
      </div>

      {/* Source tabs */}
      <div className="flex gap-1 p-3 border-b border-border bg-muted/30 overflow-x-auto shrink-0">
        {SOURCE_TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setSourceTab(tab.id)}
            className={cn(
              'flex items-center gap-1.5 px-3 py-2 rounded text-xs font-medium transition-colors whitespace-nowrap shrink-0',
              sourceTab === tab.id
                ? 'bg-primary text-primary-foreground'
                : 'text-muted-foreground hover:text-foreground hover:bg-accent'
            )}
          >
            {t(`filingSearch.tabs.${tab.id}`)}
          </button>
        ))}
      </div>

      {!SOURCE_TABS.find((tab) => tab.id === sourceTab)?.supported && (
        <div className="mx-4 mt-4 flex items-start gap-2 rounded-md bg-warning/10 border border-warning/30 p-3 shrink-0">
          <AlertTriangle size={16} className="text-warning shrink-0 mt-0.5" />
          <p className="text-xs text-warning leading-relaxed">{t('filingSearch.notSupported')}</p>
        </div>
      )}

      {/* Search input */}
      {isDirectorySource && (
        <div className="p-4 space-y-2 shrink-0">
          <div className="flex gap-2">
            <div className="relative flex-1 min-w-0">
              <Search
                size={15}
                className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground"
              />
              <input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.nativeEvent.isComposing) handleSearch()
                }}
                placeholder={t(
                  sourceTab === 'edinet'
                    ? 'filingSearch.searchPlaceholderEdinet'
                    : 'filingSearch.searchPlaceholderSecEdgar'
                )}
                className="w-full pl-9 pr-3 py-2.5 text-sm bg-card border border-border rounded-md outline-none focus:ring-2 focus:ring-ring placeholder:text-muted-foreground"
              />
            </div>
            <Button onClick={handleSearch} disabled={isSearching} size="sm" className="shrink-0">
              {isSearching ? (
                <Loader2 size={14} className="animate-spin" />
              ) : (
                t('filingSearch.searchButton')
              )}
            </Button>
          </div>
        </div>
      )}

      {/* File upload */}
      {sourceTab === 'upload-xbrl' && (
        <div className="p-4 shrink-0">
          <div
            onClick={() => fileRef.current?.click()}
            className="border-2 border-dashed border-border rounded-lg p-6 text-center cursor-pointer hover:border-primary/50 hover:bg-accent/30 transition-colors"
          >
            <Upload size={24} className="mx-auto text-muted-foreground mb-2" />
            <p className="text-sm font-medium text-foreground">
              {uploadedFile ? uploadedFile.name : t('filingSearch.dropFile')}
            </p>
            <p className="text-xs text-muted-foreground mt-1">{t('filingSearch.acceptsFiles')}</p>
            <input
              ref={fileRef}
              type="file"
              accept=".xbrl,.xml"
              className="hidden"
              onChange={(e) => {
                const f = e.target.files?.[0]
                if (f) {
                  setUploadedFile(f)
                  setLabel(f.name.replace(/\.(xbrl|xml)$/i, ''))
                  setMobileStep(1)
                }
              }}
            />
          </div>
          {uploadedFile && (
            <div className="flex items-center gap-2 mt-2 text-xs text-muted-foreground">
              <CheckCircle2 size={13} className="text-success" />
              {t('filingSearch.fileReady')}
            </div>
          )}
        </div>
      )}

      {/* Company results */}
      {isDirectorySource && (
        <div className="flex-1 px-4 pb-4 space-y-2 overflow-y-auto">
          {isSearching && (
            <div className="flex items-center gap-2 text-sm text-muted-foreground py-6 justify-center">
              <Loader2 size={16} className="animate-spin" />
              {t('filingSearch.searchingCompanies')}
            </div>
          )}
          {searchedQuery && !isSearching && companies.length === 0 && (
            <p className="text-sm text-muted-foreground text-center py-10">
              {t('filingSearch.noCompaniesFound')}
            </p>
          )}
          {!searchedQuery && !isSearching && (
            <div className="flex flex-col items-center justify-center gap-2 py-12 text-muted-foreground">
              <Search size={32} className="opacity-20" />
              <p className="text-sm">{t('filingSearch.enterCompanyPrompt')}</p>
            </div>
          )}
          {!selectedCompany &&
            companies.map((company) => (
              <button
                key={company.identifier}
                onClick={() => handleSelectCompany(company)}
                className="w-full text-left rounded-lg border border-border p-3.5 transition-all hover:border-primary/40 hover:bg-accent/30"
              >
                <div className="flex items-center gap-2 flex-wrap">
                  {company.ticker && (
                    <span className="text-sm font-semibold text-foreground">{company.ticker}</span>
                  )}
                  <Badge variant="outline" className="text-[10px] py-0 h-4">
                    {t(`filingSearch.idLabel.${company.source}`) || company.source}{' '}
                    {company.identifier}
                  </Badge>
                </div>
                <p className="text-xs text-muted-foreground mt-1 truncate">{company.name}</p>
              </button>
            ))}

          {selectedCompany && (
            <>
              <button
                onClick={() => setSelectedCompany(null)}
                className="flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground mb-2"
              >
                <ArrowLeft size={14} />
                {t('filingSearch.backToCompanies')}
              </button>
              {filingsQuery.isFetching && (
                <div className="flex items-center gap-2 text-sm text-muted-foreground py-6 justify-center">
                  <Loader2 size={16} className="animate-spin" />
                  {t('filingSearch.loadingFilings')}
                </div>
              )}
              {!filingsQuery.isFetching && filings.length === 0 && (
                <p className="text-sm text-muted-foreground text-center py-10">
                  {t('filingSearch.noFilingsFound')}
                </p>
              )}
              {filings.map((filing) => (
                <button
                  key={filing.accession_number}
                  onClick={() => handleSelectFiling(filing)}
                  className={cn(
                    'w-full text-left rounded-lg border p-3.5 transition-all',
                    selectedFiling?.accession_number === filing.accession_number
                      ? 'border-primary bg-primary/5 ring-1 ring-primary/30'
                      : 'border-border hover:border-primary/40 hover:bg-accent/30'
                  )}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <Badge variant="outline" className="text-[10px] py-0 h-4">
                          {filing.form_type}
                        </Badge>
                      </div>
                      <p className="text-[11px] text-muted-foreground/60 mt-0.5">
                        {t('filingSearch.filed', { date: filing.filing_date })}
                      </p>
                    </div>
                    {selectedFiling?.accession_number === filing.accession_number && (
                      <CheckCircle2 size={16} className="text-primary shrink-0 mt-0.5" />
                    )}
                  </div>
                </button>
              ))}
              {sourceTab === 'edinet' && !filingsQuery.isFetching && (
                <Button
                  variant="outline"
                  size="sm"
                  className="w-full text-xs"
                  onClick={() => setLookbackDays((prev) => prev + LOOKBACK_STEP_DAYS)}
                >
                  {t('filingSearch.loadMore')}
                </Button>
              )}
            </>
          )}
        </div>
      )}
    </div>
  )

  // ─── Extract panel ──────────────────────────────────────────────────────────
  const canExtract =
    (isDirectorySource && !!selectedFiling) || (sourceTab === 'upload-xbrl' && !!uploadedFile)

  const ExtractPanel = (
    <div
      className={cn(
        'flex flex-col min-h-0',
        'md:flex-1 md:overflow-y-auto',
        mobileStep === 0 ? 'hidden md:flex' : 'flex flex-1 overflow-hidden'
      )}
    >
      {!canExtract ? (
        <div className="flex-1 flex flex-col items-center justify-center gap-3 text-muted-foreground p-8">
          <Search size={40} className="opacity-20" />
          <p className="text-sm font-medium text-center">
            {t('filingSearch.extractPanel.selectFilingPrompt')}
          </p>
          <p className="text-xs text-center opacity-70">
            {t('filingSearch.extractPanel.selectFilingHint')}
          </p>
        </div>
      ) : (
        <>
          <div className="p-4 md:p-6 border-b border-border shrink-0">
            <button
              onClick={handleBackToSearch}
              className="md:hidden flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground mb-3"
            >
              <ArrowLeft size={14} />
              {t('filingSearch.extractPanel.backToResults')}
            </button>
            <div className="flex items-start gap-3">
              <div className="flex-1 min-w-0">
                <h2 className="text-base md:text-lg font-semibold text-foreground leading-tight">
                  {sourceTab === 'upload-xbrl' ? uploadedFile?.name : selectedCompany?.name}
                </h2>
                {isDirectorySource && selectedCompany && selectedFiling && (
                  <>
                    <div className="flex items-center gap-1.5 flex-wrap mt-1.5">
                      {selectedCompany.ticker && (
                        <Badge variant="secondary" className="text-xs">
                          {selectedCompany.ticker}
                        </Badge>
                      )}
                      <Badge variant="outline" className="text-xs">
                        {selectedFiling.form_type}
                      </Badge>
                    </div>
                    <p className="text-xs text-muted-foreground mt-1.5">
                      {t('filingSearch.extractPanel.filedLabel', {
                        idLabel,
                        identifier: selectedCompany.identifier,
                        date: selectedFiling.filing_date,
                      })}
                    </p>
                  </>
                )}
              </div>
              <Button
                size="icon"
                variant="ghost"
                className="shrink-0 hidden md:flex"
                onClick={() => {
                  setSelectedFiling(null)
                  setUploadedFile(null)
                }}
              >
                <X size={16} />
              </Button>
            </div>
          </div>

          <div className="flex-1 p-4 md:p-6 space-y-3 overflow-y-auto">
            <div>
              <label className="text-xs font-medium text-muted-foreground" htmlFor="extraction-label">
                {t('filingSearch.extractPanel.extractionNameLabel')}
              </label>
              <input
                id="extraction-label"
                value={label}
                onChange={(e) => setLabel(e.target.value)}
                placeholder={t('filingSearch.extractPanel.extractionNamePlaceholder')}
                className="w-full mt-1 px-3 py-2 text-sm bg-card border border-border rounded-md outline-none focus:ring-2 focus:ring-ring placeholder:text-muted-foreground"
              />
              <p className="text-xs text-muted-foreground mt-1">
                {t('filingSearch.extractPanel.extractionNameHint')}
              </p>
            </div>
            <p className="text-sm text-muted-foreground">
              {t('filingSearch.extractPanel.bodyText')}
            </p>
          </div>

          <div className="p-4 md:p-6 border-t border-border bg-card/50 shrink-0">
            <div className="flex items-center justify-end gap-3">
              <Button
                onClick={() => extractMutation.mutate()}
                disabled={extractMutation.isPending}
                className="gap-2 shrink-0"
              >
                {extractMutation.isPending ? (
                  <Loader2 size={15} className="animate-spin" />
                ) : (
                  <Plus size={15} />
                )}
                {extractMutation.isPending
                  ? t('filingSearch.extractPanel.extracting')
                  : t('filingSearch.extractPanel.launchExtraction')}
              </Button>
            </div>
          </div>
        </>
      )}
    </div>
  )

  return (
    <div className="flex flex-col md:flex-row h-full min-h-0 overflow-hidden">
      {SearchPanel}
      {ExtractPanel}
    </div>
  )
}
