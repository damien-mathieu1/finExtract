'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Download, Eye, ChevronDown, BarChart2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import { useTranslation } from '@/lib/i18n'
import { getExtraction, combineExtractions, downloadExport, downloadCombinedExport, listExtractions } from '@/lib/api/extractions'
import { toExtractionResult } from '@/lib/statement-transform'
import type { SheetRow } from '@/lib/types'
import { toast } from 'sonner'
import type { AppPage } from '@/components/app-sidebar'

interface DataViewerPageProps {
  selectedExtractionIds: number[]
  onNavigate: (page: AppPage) => void
}

type SheetKey = 'is' | 'bs' | 'cf'

const SHEET_META: Record<SheetKey, { color: string; bgColor: string }> = {
  is: { color: 'text-chart-1', bgColor: 'bg-chart-1/10' },
  bs: { color: 'text-chart-2', bgColor: 'bg-chart-2/10' },
  cf: { color: 'text-chart-3', bgColor: 'bg-chart-3/10' },
}

function formatNum(val: string | number) {
  if (typeof val === 'string') return val
  if (val === 0) return '—'
  const abs = Math.abs(val)
  const sign = val < 0 ? '-' : ''
  if (abs >= 1_000_000) return `${sign}$${(abs / 1_000).toLocaleString(undefined, { maximumFractionDigits: 0 })}M`
  if (abs >= 1_000) return `${sign}$${abs.toLocaleString(undefined, { maximumFractionDigits: 0 })}`
  return `${sign}${val}`
}

function DataTable({ rows, years }: { rows: SheetRow[]; years: string[] }) {
  const { t } = useTranslation()
  if (rows.length === 0) {
    return (
      <p className="text-xs text-muted-foreground py-8 text-center">
        {t('dataViewer.noDataForSheet')}
      </p>
    )
  }
  return (
    <div className="overflow-x-auto -mx-4 md:mx-0">
      <table className="w-full text-xs min-w-[320px]">
        <thead>
          <tr className="border-b border-border">
            <th className="text-left py-2 px-4 md:px-3 font-semibold text-muted-foreground sticky left-0 bg-background z-10 min-w-[140px]">
              {t('dataViewer.field')}
            </th>
            <th className="text-left py-2 px-3 font-mono text-muted-foreground/60 hidden lg:table-cell min-w-[180px]">
              {t('dataViewer.xbrlTag')}
            </th>
            {years.map((y) => (
              <th
                key={y}
                className="text-right py-2 px-4 md:px-3 font-semibold text-foreground min-w-[90px]"
              >
                {y}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr
              key={i}
              className={cn(
                'border-b border-border/50',
                i % 2 === 0 ? 'bg-transparent' : 'bg-muted/20'
              )}
            >
              <td className="py-2.5 px-4 md:px-3 font-medium text-foreground sticky left-0 bg-inherit z-10">
                {row.label}
              </td>
              <td className="py-2.5 px-3 font-mono text-muted-foreground/50 text-[10px] hidden lg:table-cell truncate max-w-0">
                {row.xbrlTag}
              </td>
              {years.map((y) => {
                const val = row[y]
                const isNeg = typeof val === 'number' && val < 0
                return (
                  <td
                    key={y}
                    className={cn(
                      'py-2.5 px-4 md:px-3 text-right tabular-nums',
                      isNeg ? 'text-destructive' : 'text-foreground'
                    )}
                  >
                    {val !== undefined ? formatNum(val) : '—'}
                  </td>
                )
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export function DataViewerPage({ selectedExtractionIds, onNavigate }: DataViewerPageProps) {
  const { t } = useTranslation()
  const [activeSheet, setActiveSheet] = useState<SheetKey>('is')
  const [selectorOpen, setSelectorOpen] = useState(false)
  const [localIds, setLocalIds] = useState<number[]>(selectedExtractionIds)

  const { data: allExtractions = [] } = useQuery({
    queryKey: ['extractions'],
    queryFn: () => listExtractions({}),
  })

  const { data: statements = [] } = useQuery({
    queryKey: ['extraction-detail', localIds],
    queryFn: () =>
      localIds.length > 1
        ? combineExtractions(localIds)
        : localIds.length === 1
          ? getExtraction(localIds[0]).then((s) => [s])
          : Promise.resolve([]),
    enabled: localIds.length > 0,
  })

  const result = toExtractionResult(statements)
  const years = Array.from(new Set(statements.map((s) => s.period_label))).sort()

  async function handleExportXlsx() {
    if (localIds.length === 0) return
    try {
      if (localIds.length > 1) await downloadCombinedExport(localIds, 'excel')
      else await downloadExport(localIds[0], 'excel')
      toast.success(t('dataViewer.toasts.exportSuccess'))
    } catch {
      toast.error(t('dataViewer.toasts.exportFailed'))
    }
  }

  return (
    <div className="flex flex-col h-full min-h-0">
      {/* Header */}
      <div className="p-4 md:p-6 border-b border-border shrink-0">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <h1 className="text-lg md:text-xl font-semibold text-foreground">
              {t('dataViewer.title')}
            </h1>
            <p className="text-sm text-muted-foreground mt-0.5 truncate">
              {localIds.length === 0
                ? t('dataViewer.noExtractionsSelected')
                : localIds.length === 1
                  ? statements[0]?.company_name
                  : t('dataViewer.extractionsMerged', { count: localIds.length })}
            </p>
          </div>
          <div className="flex items-center gap-2 shrink-0 flex-wrap justify-end">
            <Button
              variant="outline"
              size="sm"
              onClick={() => onNavigate('charts')}
              className="gap-1.5 h-8 text-xs"
            >
              <BarChart2 size={13} />
              {t('dataViewer.charts')}
            </Button>
            <Button
              size="sm"
              onClick={handleExportXlsx}
              disabled={localIds.length === 0}
              className="gap-1.5 h-8 text-xs"
            >
              <Download size={13} />
              {t('dataViewer.xlsx')}
            </Button>
          </div>
        </div>

        {/* Extraction selector */}
        <div className="mt-3">
          <button
            onClick={() => setSelectorOpen(!selectorOpen)}
            className="flex items-center gap-2 text-xs text-muted-foreground hover:text-foreground transition-colors"
          >
            <Eye size={13} />
            {localIds.length === 0
              ? t('dataViewer.selectExtractionsToView')
              : t('dataViewer.extractionsSelectedCount', { count: localIds.length })}
            <ChevronDown
              size={13}
              className={cn('transition-transform', selectorOpen && 'rotate-180')}
            />
          </button>
          {selectorOpen && (
            <div className="mt-2 border border-border rounded-lg overflow-hidden max-h-52 overflow-y-auto">
              {allExtractions.length === 0 && (
                <p className="text-xs text-muted-foreground p-3 text-center">
                  {t('dataViewer.noExtractionsYet')}
                </p>
              )}
              {allExtractions.map((ext) => (
                <label
                  key={ext.id}
                  className={cn(
                    'flex items-center gap-3 px-4 py-2.5 cursor-pointer transition-colors text-sm border-b border-border/50 last:border-0',
                    localIds.includes(ext.id) ? 'bg-primary/5' : 'hover:bg-accent/30'
                  )}
                >
                  <input
                    type="checkbox"
                    className="accent-primary w-3.5 h-3.5 shrink-0"
                    checked={localIds.includes(ext.id)}
                    onChange={() => {
                      setLocalIds((prev) =>
                        prev.includes(ext.id) ? prev.filter((i) => i !== ext.id) : [...prev, ext.id]
                      )
                    }}
                  />
                  <div className="flex-1 min-w-0">
                    <span className="font-medium text-foreground truncate block">
                      {ext.company_name}
                    </span>
                    <span className="text-xs text-muted-foreground">{ext.period_label}</span>
                  </div>
                </label>
              ))}
            </div>
          )}
        </div>
      </div>

      {localIds.length === 0 ? (
        <div className="flex-1 flex flex-col items-center justify-center gap-3 text-muted-foreground p-6">
          <Eye size={40} className="opacity-20" />
          <p className="text-sm font-medium">{t('dataViewer.noExtractionsSelected')}</p>
          <p className="text-xs opacity-70 text-center">{t('dataViewer.useSelectorHint')}</p>
        </div>
      ) : (
        <>
          {/* Sheet tabs */}
          <div className="flex border-b border-border px-4 md:px-6 shrink-0 overflow-x-auto">
            {(Object.entries(SHEET_META) as [SheetKey, (typeof SHEET_META)[SheetKey]][]).map(
              ([key, meta]) => {
                const count = result[key].length
                return (
                  <button
                    key={key}
                    onClick={() => setActiveSheet(key)}
                    className={cn(
                      'flex items-center gap-1.5 md:gap-2 px-3 md:px-4 py-3 text-xs md:text-sm font-medium border-b-2 transition-colors whitespace-nowrap shrink-0',
                      activeSheet === key
                        ? 'border-primary text-foreground'
                        : 'border-transparent text-muted-foreground hover:text-foreground'
                    )}
                  >
                    <span className="md:hidden">{t(`dataViewer.sheets.${key}.short`)}</span>
                    <span className="hidden md:inline">{t(`dataViewer.sheets.${key}.label`)}</span>
                    <span
                      className={cn(
                        'text-[10px] md:text-[11px] px-1 md:px-1.5 py-0.5 rounded-full font-medium',
                        activeSheet === key
                          ? `${meta.bgColor} ${meta.color}`
                          : 'bg-muted text-muted-foreground'
                      )}
                    >
                      {count}
                    </span>
                  </button>
                )
              }
            )}
          </div>

          {/* Summary chips */}
          <div className="px-4 md:px-6 py-2.5 flex items-center gap-2 border-b border-border/50 bg-muted/20 flex-wrap shrink-0">
            {Array.from(new Set(statements.map((s) => s.company_name))).map((name) => (
              <Badge key={name} variant="secondary" className="text-xs gap-1">
                <span className="font-semibold">{name}</span>
              </Badge>
            ))}
            {years.length > 0 && (
              <span className="text-xs text-muted-foreground ml-1">· {years.join(', ')}</span>
            )}
          </div>

          {/* Data table */}
          <div className="flex-1 overflow-y-auto px-4 md:px-6 py-4">
            <DataTable rows={result[activeSheet]} years={years} />
          </div>
        </>
      )}
    </div>
  )
}
