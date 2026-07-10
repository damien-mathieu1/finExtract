'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { GitMerge, Download, Eye, Search, CheckCircle2, ChevronRight, ChevronDown } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import { listExtractions, downloadCombinedExport, downloadExport } from '@/lib/api/extractions'
import type { ExtractionSummaryResponse } from '@/lib/api/types'
import { toast } from 'sonner'
import type { AppPage } from '@/components/app-sidebar'
import { format } from 'date-fns'

interface ExtractionsPageProps {
  onNavigate: (page: AppPage, selectedIds?: number[]) => void
}

export function ExtractionsPage({ onNavigate }: ExtractionsPageProps) {
  const { data: extractions = [] } = useQuery({
    queryKey: ['extractions'],
    queryFn: () => listExtractions({}),
  })
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set())
  const [searchQuery, setSearchQuery] = useState('')
  const [expanded, setExpanded] = useState<Set<string>>(new Set())

  const filtered = extractions.filter((e) =>
    e.company_name.toLowerCase().includes(searchQuery.toLowerCase())
  )

  // One filing (source_reference) can yield several periods (comparative
  // years from the same XBRL doc) - group them so the table shows one row
  // per filing instead of one row per period.
  const groups = Object.values(
    filtered.reduce<Record<string, { key: string; items: ExtractionSummaryResponse[] }>>(
      (acc, ext) => {
        const key = ext.source_reference
        acc[key] ??= { key, items: [] }
        acc[key].items.push(ext)
        return acc
      },
      {}
    )
  ).map((g) => ({
    ...g,
    items: g.items.sort((a, b) => a.fiscal_year - b.fiscal_year),
    displayName: g.items[0]?.label || g.items[0]?.source_reference,
  }))

  function toggleExpand(key: string) {
    setExpanded((prev) => {
      const next = new Set(prev)
      next.has(key) ? next.delete(key) : next.add(key)
      return next
    })
  }

  function toggleSelect(id: number) {
    setSelectedIds((prev) => {
      const next = new Set(prev)
      next.has(id) ? next.delete(id) : next.add(id)
      return next
    })
  }

  function toggleAll() {
    if (selectedIds.size === filtered.length) {
      setSelectedIds(new Set())
    } else {
      setSelectedIds(new Set(filtered.map((e) => e.id)))
    }
  }

  async function handleExportSelected() {
    if (selectedIds.size === 0) {
      toast.error('Please select extractions to export.')
      return
    }
    try {
      await downloadCombinedExport(Array.from(selectedIds), 'excel')
      toast.success('XLSX export ready')
    } catch {
      toast.error('Export failed')
    }
  }

  async function handleExportSingle(id: number) {
    try {
      await downloadExport(id, 'excel')
    } catch {
      toast.error('Export failed')
    }
  }

  function handleMergeAndView() {
    if (selectedIds.size < 2) {
      toast.error('Select at least 2 extractions to merge.')
      return
    }
    onNavigate('viewer', Array.from(selectedIds))
  }

  function handleViewSingle(id: number) {
    onNavigate('viewer', [id])
  }

  return (
    <div className="flex flex-col h-full min-h-0">
      {/* Header */}
      <div className="p-4 md:p-6 border-b border-border shrink-0">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <h1 className="text-lg md:text-xl font-semibold text-foreground">Extractions</h1>
            <p className="text-sm text-muted-foreground mt-0.5">
              {groups.length} filing{groups.length !== 1 ? 's' : ''} ({extractions.length} period
              {extractions.length !== 1 ? 's' : ''}) · Select to merge, export, or view
            </p>
          </div>
        </div>

        {/* Bulk actions */}
        {selectedIds.size > 0 && (
          <div className="flex items-center gap-2 flex-wrap mt-3 pt-3 border-t border-border/60">
            <span className="text-xs text-muted-foreground font-medium">
              {selectedIds.size} selected
            </span>
            {selectedIds.size >= 2 && (
              <Button
                variant="outline"
                size="sm"
                onClick={handleMergeAndView}
                className="gap-1.5 h-8 text-xs"
              >
                <GitMerge size={13} />
                Merge & View
              </Button>
            )}
            <Button size="sm" onClick={handleExportSelected} className="gap-1.5 h-8 text-xs">
              <Download size={13} />
              Export XLSX
            </Button>
          </div>
        )}

        {/* Search */}
        <div className="relative mt-3">
          <Search
            size={14}
            className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground"
          />
          <input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Filter extractions…"
            className="w-full pl-9 pr-3 py-2.5 text-sm bg-card border border-border rounded-md outline-none focus:ring-2 focus:ring-ring placeholder:text-muted-foreground"
          />
        </div>
      </div>

      {/* Desktop table header */}
      <div className="hidden md:flex px-6 py-2 bg-muted/30 border-b border-border text-xs text-muted-foreground font-medium items-center gap-3 shrink-0">
        <input
          type="checkbox"
          className="accent-primary w-3.5 h-3.5"
          checked={filtered.length > 0 && selectedIds.size === filtered.length}
          onChange={toggleAll}
          aria-label="Select all"
        />
        <span className="flex-1">Company</span>
        <span className="w-20 text-center">Period</span>
        <span className="w-24 text-center">Standard</span>
        <span className="w-24 text-right">Extracted</span>
        <span className="w-24 text-right">Actions</span>
      </div>

      {/* List */}
      <div className="flex-1 overflow-y-auto">
        {filtered.length === 0 && (
          <div className="flex flex-col items-center justify-center gap-3 py-20 text-muted-foreground">
            <GitMerge size={36} className="opacity-20" />
            <p className="text-sm font-medium">No extractions yet</p>
            <p className="text-xs opacity-70">
              Run an extraction from Filing Search to see it here
            </p>
          </div>
        )}

        {groups.map((group) => {
          const isExpanded = group.items.length === 1 || expanded.has(group.key)
          return (
            <div key={group.key}>
              {group.items.length > 1 && (
                <div className="w-full flex items-center gap-2 px-4 md:px-6 py-2.5 border-b border-border/60 bg-muted/20 hover:bg-muted/40 transition-colors">
                  <input
                    type="checkbox"
                    className="accent-primary w-3.5 h-3.5 shrink-0"
                    checked={group.items.every((e) => selectedIds.has(e.id))}
                    ref={(el) => {
                      if (el) {
                        const selectedCount = group.items.filter((e) => selectedIds.has(e.id)).length
                        el.indeterminate = selectedCount > 0 && selectedCount < group.items.length
                      }
                    }}
                    onChange={() => {
                      const allSelected = group.items.every((e) => selectedIds.has(e.id))
                      setSelectedIds((prev) => {
                        const next = new Set(prev)
                        for (const e of group.items) {
                          allSelected ? next.delete(e.id) : next.add(e.id)
                        }
                        return next
                      })
                    }}
                    aria-label={`Select all periods for ${group.displayName}`}
                  />
                  <button
                    onClick={() => toggleExpand(group.key)}
                    className="flex-1 flex items-center gap-2 min-w-0 text-left"
                  >
                    {isExpanded ? (
                      <ChevronDown size={14} className="text-muted-foreground shrink-0" />
                    ) : (
                      <ChevronRight size={14} className="text-muted-foreground shrink-0" />
                    )}
                    <span className="text-sm font-medium text-foreground truncate">
                      {group.displayName}
                    </span>
                    <Badge variant="secondary" className="text-[10px] shrink-0">
                      {group.items.length} periods
                    </Badge>
                  </button>
                  {group.items.some((e) => selectedIds.has(e.id)) && (
                    <Button
                      size="sm"
                      variant="outline"
                      className="h-7 text-xs gap-1.5 shrink-0"
                      onClick={() => onNavigate('viewer', group.items.map((e) => e.id))}
                    >
                      <GitMerge size={12} />
                      Merge & View
                    </Button>
                  )}
                </div>
              )}

              {isExpanded &&
                group.items.map((ext: ExtractionSummaryResponse) => (
                  <div key={ext.id}>
            {/* Desktop row */}
            <div
              className={cn(
                'hidden md:flex items-center gap-3 px-6 py-3.5 border-b border-border/60 transition-colors',
                selectedIds.has(ext.id) ? 'bg-primary/5' : 'hover:bg-accent/30'
              )}
            >
              <input
                type="checkbox"
                className="accent-primary w-3.5 h-3.5 shrink-0"
                checked={selectedIds.has(ext.id)}
                onChange={() => toggleSelect(ext.id)}
                aria-label={`Select ${ext.company_name}`}
              />
              <div className="flex-1 min-w-0">
                <div className="text-sm font-medium text-foreground truncate">
                  {group.items.length > 1 ? ext.company_name : ext.label || ext.company_name}
                </div>
                <div className="flex items-center gap-2 mt-0.5">
                  <span className="text-xs text-muted-foreground truncate">
                    {group.items.length > 1 ? ext.period_label : ext.source_reference}
                  </span>
                  <CheckCircle2 size={11} className="text-success shrink-0" />
                </div>
              </div>
              <span className="w-20 text-center text-xs text-muted-foreground">
                {ext.period_label}
              </span>
              <span className="w-24 text-center">
                <Badge variant="outline" className="text-[10px]">
                  {ext.accounting_standard}
                </Badge>
              </span>
              <span className="w-24 text-right text-xs text-muted-foreground">
                {format(new Date(ext.extracted_at), 'MMM d, HH:mm')}
              </span>
              <div className="w-24 flex items-center justify-end gap-1">
                <Button
                  size="icon"
                  variant="ghost"
                  className="h-7 w-7"
                  title="View data"
                  onClick={() => handleViewSingle(ext.id)}
                >
                  <Eye size={14} />
                </Button>
                <Button
                  size="icon"
                  variant="ghost"
                  className="h-7 w-7"
                  title="Export XLSX"
                  onClick={() => handleExportSingle(ext.id)}
                >
                  <Download size={14} />
                </Button>
              </div>
            </div>

            {/* Mobile card */}
            <div
              className={cn(
                'md:hidden flex gap-3 px-4 py-3.5 border-b border-border/60 transition-colors',
                selectedIds.has(ext.id) ? 'bg-primary/5' : ''
              )}
            >
              <input
                type="checkbox"
                className="accent-primary w-4 h-4 mt-0.5 shrink-0"
                checked={selectedIds.has(ext.id)}
                onChange={() => toggleSelect(ext.id)}
                aria-label={`Select ${ext.company_name}`}
              />
              <div className="flex-1 min-w-0">
                <div className="flex items-start justify-between gap-2">
                  <div className="min-w-0">
                    <p className="text-sm font-semibold text-foreground leading-tight truncate">
                      {group.items.length > 1 ? ext.company_name : ext.label || ext.company_name}
                      <span className="text-muted-foreground font-normal ml-1">
                        {ext.period_label}
                      </span>
                    </p>
                  </div>
                  <Badge variant="outline" className="text-[10px]">
                    {ext.accounting_standard}
                  </Badge>
                </div>

                <div className="flex items-center gap-2 mt-2 flex-wrap">
                  <span className="text-[11px] text-muted-foreground/60">
                    {format(new Date(ext.extracted_at), 'MMM d, HH:mm')}
                  </span>
                </div>

                <div className="flex items-center gap-2 mt-2.5">
                  <Button
                    size="sm"
                    variant="outline"
                    className="h-7 text-xs gap-1.5 px-2.5"
                    onClick={() => handleViewSingle(ext.id)}
                  >
                    <Eye size={12} />
                    View
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    className="h-7 text-xs gap-1.5 px-2.5"
                    onClick={() => handleExportSingle(ext.id)}
                  >
                    <Download size={12} />
                    XLSX
                  </Button>
                </div>
              </div>
                  </div>
                  </div>
                ))}
            </div>
          )
        })}
      </div>
    </div>
  )
}
