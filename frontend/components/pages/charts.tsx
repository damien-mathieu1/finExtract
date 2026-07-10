'use client'

import { useState, useMemo } from 'react'
import { useQuery, useQueries } from '@tanstack/react-query'
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  LineChart,
  Line,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from 'recharts'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import { listExtractions, getExtraction } from '@/lib/api/extractions'
import type { ExtractionSummaryResponse, FinancialStatementResponse } from '@/lib/api/types'
import { BarChart2, TrendingUp, Activity, ChevronDown, SlidersHorizontal, X } from 'lucide-react'

type ChartType = 'bar' | 'line' | 'area'
type MetricKey = { label: string; xbrlTag: string; sheet: 'is' | 'bs' | 'cf' }

const CHART_TYPES: { id: ChartType; label: string; icon: React.ReactNode }[] = [
  { id: 'bar', label: 'Bar', icon: <BarChart2 size={14} /> },
  { id: 'line', label: 'Line', icon: <TrendingUp size={14} /> },
  { id: 'area', label: 'Area', icon: <Activity size={14} /> },
]

const CATEGORY_TO_SHEET = { income_statement: 'is', balance_sheet: 'bs', cash_flow: 'cf' } as const

const METRIC_COLORS = [
  'var(--color-chart-1)',
  'var(--color-chart-2)',
  'var(--color-chart-3)',
  'var(--color-chart-4)',
  'var(--color-chart-5)',
]

// One filing (source_reference) can yield several periods (comparative years
// from the same XBRL doc) - group them so pickers show one entry per filing.
function groupByFiling(extractions: ExtractionSummaryResponse[]) {
  const byKey = new Map<string, ExtractionSummaryResponse[]>()
  for (const ext of extractions) {
    const list = byKey.get(ext.source_reference) ?? []
    list.push(ext)
    byKey.set(ext.source_reference, list)
  }
  return Array.from(byKey.entries()).map(([key, items]) => ({
    key,
    items: items.sort((a, b) => a.fiscal_year - b.fiscal_year),
    displayName: items[0]?.label || items[0]?.source_reference,
  }))
}

function formatYAxis(val: number) {
  const abs = Math.abs(val)
  if (abs >= 1_000_000) return `${val < 0 ? '-' : ''}$${(abs / 1_000).toFixed(0)}M`
  if (abs >= 1_000) return `${val < 0 ? '-' : ''}$${abs.toFixed(0)}`
  return `${val}`
}

function formatTooltipVal(val: number) {
  const abs = Math.abs(val)
  const sign = val < 0 ? '-' : ''
  if (abs >= 1_000) return `${sign}$${abs.toLocaleString(undefined, { maximumFractionDigits: 0 })}M`
  return `${sign}${val}`
}

function CustomTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-popover border border-border rounded-lg shadow-lg p-3 text-xs min-w-36 max-w-52">
      <p className="font-semibold text-foreground mb-2">{label}</p>
      {payload.map((p: any, i: number) => (
        <div key={i} className="flex items-center justify-between gap-3">
          <span className="flex items-center gap-1.5 text-muted-foreground min-w-0 truncate">
            <span className="w-2 h-2 rounded-sm shrink-0" style={{ backgroundColor: p.color }} />
            <span className="truncate">{p.name}</span>
          </span>
          <span className="font-medium text-foreground tabular-nums shrink-0">
            {formatTooltipVal(p.value)}
          </span>
        </div>
      ))}
    </div>
  )
}

function ControlsContent({
  completed,
  selectedIds,
  setSelectedIds,
  selectedNames,
  chartType,
  setChartType,
  availableMetrics,
  selectedMetrics,
  toggleMetric,
  selectorOpen,
  setSelectorOpen,
}: {
  completed: ExtractionSummaryResponse[]
  selectedIds: number[]
  setSelectedIds: React.Dispatch<React.SetStateAction<number[]>>
  selectedNames: string[]
  chartType: ChartType
  setChartType: (t: ChartType) => void
  availableMetrics: MetricKey[]
  selectedMetrics: Set<string>
  toggleMetric: (tag: string) => void
  selectorOpen: boolean
  setSelectorOpen: (v: boolean) => void
}) {
  return (
    <>
      <div className="p-4 border-b border-border">
        <p className="text-xs font-medium text-muted-foreground mb-2 uppercase tracking-wider">
          Chart Type
        </p>
        <div className="flex gap-1">
          {CHART_TYPES.map((t) => (
            <button
              key={t.id}
              onClick={() => setChartType(t.id)}
              className={cn(
                'flex items-center gap-1.5 px-3 py-2 rounded text-xs font-medium transition-colors flex-1 justify-center',
                chartType === t.id
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-muted text-muted-foreground hover:text-foreground'
              )}
            >
              {t.icon} {t.label}
            </button>
          ))}
        </div>
      </div>

      <div className="p-4 border-b border-border">
        <button
          className="flex items-center justify-between w-full text-xs font-medium text-muted-foreground mb-2 uppercase tracking-wider hover:text-foreground"
          onClick={() => setSelectorOpen(!selectorOpen)}
        >
          Extractions
          <ChevronDown size={13} className={cn('transition-transform', selectorOpen && 'rotate-180')} />
        </button>
        {selectorOpen && (
          <div className="space-y-2 mb-2">
            {groupByFiling(completed).map((group) => {
              const groupIds = group.items.map((e) => e.id)
              const allSelected = groupIds.every((id) => selectedIds.includes(id))
              const someSelected = groupIds.some((id) => selectedIds.includes(id))
              return (
                <div key={group.key}>
                  <label className="flex items-center gap-2 cursor-pointer py-1">
                    <input
                      type="checkbox"
                      className="accent-primary w-3.5 h-3.5 shrink-0"
                      checked={allSelected}
                      ref={(el) => {
                        if (el) el.indeterminate = someSelected && !allSelected
                      }}
                      onChange={() =>
                        setSelectedIds((prev) =>
                          allSelected
                            ? prev.filter((id) => !groupIds.includes(id))
                            : Array.from(new Set([...prev, ...groupIds]))
                        )
                      }
                    />
                    <span className="text-xs font-medium text-foreground truncate">
                      {group.displayName}
                    </span>
                  </label>
                  <div className="pl-5 space-y-1">
                    {group.items.map((ext) => (
                      <label key={ext.id} className="flex items-center gap-2 cursor-pointer py-0.5">
                        <input
                          type="checkbox"
                          className="accent-primary w-3.5 h-3.5 shrink-0"
                          checked={selectedIds.includes(ext.id)}
                          onChange={() =>
                            setSelectedIds((prev) =>
                              prev.includes(ext.id)
                                ? prev.filter((i) => i !== ext.id)
                                : [...prev, ext.id]
                            )
                          }
                        />
                        <span className="text-xs text-muted-foreground truncate">
                          {ext.period_label}
                        </span>
                      </label>
                    ))}
                  </div>
                </div>
              )
            })}
          </div>
        )}
        <div className="flex flex-wrap gap-1">
          {selectedNames.map((name) => (
            <Badge key={name} variant="secondary" className="text-[10px]">
              {name}
            </Badge>
          ))}
        </div>
      </div>

      <div className="p-4 flex-1 overflow-y-auto">
        <p className="text-xs font-medium text-muted-foreground mb-2 uppercase tracking-wider">
          Metrics
        </p>
        {availableMetrics.length === 0 && (
          <p className="text-xs text-muted-foreground">
            Select extractions above to see available metrics
          </p>
        )}
        <div className="space-y-1">
          {availableMetrics.map((m, i) => (
            <label
              key={m.xbrlTag}
              className={cn(
                'flex items-center gap-2 cursor-pointer rounded px-2 py-2 transition-colors',
                selectedMetrics.has(m.xbrlTag) ? 'bg-accent/50' : 'hover:bg-accent/30'
              )}
            >
              <input
                type="checkbox"
                className="accent-primary w-3 h-3 shrink-0"
                checked={selectedMetrics.has(m.xbrlTag)}
                onChange={() => toggleMetric(m.xbrlTag)}
              />
              <div className="min-w-0 flex-1">
                <p
                  className={cn(
                    'text-xs truncate font-medium',
                    selectedMetrics.has(m.xbrlTag) ? 'text-foreground' : 'text-muted-foreground'
                  )}
                >
                  {m.label}
                </p>
                <p className="text-[10px] text-muted-foreground/50 uppercase tracking-wide">
                  {m.sheet === 'is' ? 'IS' : m.sheet === 'bs' ? 'BS' : 'CF'}
                </p>
              </div>
              {selectedMetrics.has(m.xbrlTag) && (
                <span
                  className="w-2.5 h-2.5 rounded-sm shrink-0"
                  style={{ backgroundColor: METRIC_COLORS[i % METRIC_COLORS.length] }}
                />
              )}
            </label>
          ))}
        </div>
      </div>
    </>
  )
}

export function ChartsPage() {
  const { data: completed = [] } = useQuery({
    queryKey: ['extractions'],
    queryFn: () => listExtractions({}),
  })

  const [selectedIds, setSelectedIds] = useState<number[]>([])
  const [chartType, setChartType] = useState<ChartType>('bar')
  const [selectedMetrics, setSelectedMetrics] = useState<Set<string>>(new Set())
  const [selectorOpen, setSelectorOpen] = useState(false)
  const [mobileControlsOpen, setMobileControlsOpen] = useState(false)

  const statementQueries = useQueries({
    queries: selectedIds.map((id) => ({
      queryKey: ['extraction-detail', [id]],
      queryFn: () => getExtraction(id),
    })),
  })
  const statements: FinancialStatementResponse[] = statementQueries
    .map((q) => q.data)
    .filter((s): s is FinancialStatementResponse => !!s)

  const multiCompany = new Set(statements.map((s) => s.company_name)).size > 1
  const selectedNames = Array.from(new Set(statements.map((s) => s.company_name)))

  const availableMetrics = useMemo(() => {
    const map = new Map<string, MetricKey>()
    for (const statement of statements) {
      for (const item of statement.line_items) {
        if (!map.has(item.original_label)) {
          map.set(item.original_label, {
            label: item.field_name,
            xbrlTag: item.original_label,
            sheet: CATEGORY_TO_SHEET[item.category],
          })
        }
      }
    }
    return Array.from(map.values())
  }, [statements])

  const chartData = useMemo(() => {
    const years = Array.from(new Set(statements.map((s) => s.period_label))).sort()
    return years.map((year) => {
      const point: Record<string, string | number> = { year }
      for (const statement of statements) {
        if (statement.period_label !== year) continue
        for (const item of statement.line_items) {
          if (!selectedMetrics.has(item.original_label) || item.value === null) continue
          const seriesKey = multiCompany
            ? `${statement.company_name} · ${item.field_name}`
            : item.field_name
          point[seriesKey] = item.value
        }
      }
      return point
    })
  }, [statements, selectedMetrics, multiCompany])

  const seriesKeys = useMemo(() => {
    if (chartData.length === 0) return []
    const keys = new Set<string>()
    chartData.forEach((point) => Object.keys(point).forEach((k) => k !== 'year' && keys.add(k)))
    return Array.from(keys)
  }, [chartData])

  function toggleMetric(tag: string) {
    setSelectedMetrics((prev) => {
      const next = new Set(prev)
      next.has(tag) ? next.delete(tag) : next.add(tag)
      return next
    })
  }

  const ChartComponent = chartType === 'bar' ? BarChart : chartType === 'line' ? LineChart : AreaChart

  const controlsProps = {
    completed,
    selectedIds,
    setSelectedIds,
    selectedNames,
    chartType,
    setChartType,
    availableMetrics,
    selectedMetrics,
    toggleMetric,
    selectorOpen,
    setSelectorOpen,
  }

  return (
    <div className="flex flex-col md:flex-row h-full min-h-0 overflow-hidden">
      <div className="hidden md:flex w-64 shrink-0 border-r border-border flex-col overflow-y-auto">
        <div className="p-4 border-b border-border shrink-0">
          <h2 className="text-sm font-semibold text-foreground">Chart Settings</h2>
        </div>
        <ControlsContent {...controlsProps} />
      </div>

      <div className="flex-1 flex flex-col overflow-hidden min-h-0">
        <div className="p-4 md:p-6 border-b border-border shrink-0">
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0">
              <h1 className="text-lg md:text-xl font-semibold text-foreground">Figures</h1>
              <p className="text-sm text-muted-foreground mt-0.5 truncate">
                {selectedIds.length === 0
                  ? 'Select extractions to visualize'
                  : selectedNames.join(' · ')}
              </p>
            </div>
            <Button
              variant="outline"
              size="sm"
              className="md:hidden gap-1.5 h-8 text-xs shrink-0"
              onClick={() => setMobileControlsOpen(true)}
            >
              <SlidersHorizontal size={13} />
              Settings
              {selectedMetrics.size > 0 && (
                <span className="ml-0.5 bg-primary/15 text-primary rounded-full px-1 text-[10px] font-medium">
                  {selectedMetrics.size}
                </span>
              )}
            </Button>
          </div>
          {selectedNames.length > 0 && (
            <div className="flex gap-1.5 flex-wrap mt-2 md:hidden">
              {selectedNames.map((name) => (
                <Badge key={name} variant="secondary" className="text-[10px]">
                  {name}
                </Badge>
              ))}
            </div>
          )}
        </div>

        {selectedIds.length === 0 || chartData.length === 0 || seriesKeys.length === 0 ? (
          <div className="flex-1 flex flex-col items-center justify-center gap-3 text-muted-foreground p-6">
            <BarChart2 size={48} className="opacity-15" />
            <p className="text-sm font-medium text-center">
              {selectedIds.length === 0
                ? 'Tap Settings to select extractions'
                : 'Select at least one metric in Settings'}
            </p>
          </div>
        ) : (
          <div className="flex-1 p-4 md:p-6 overflow-y-auto space-y-4 md:space-y-8">
            <div className="bg-card border border-border rounded-xl p-4 md:p-6">
              <h3 className="text-sm font-semibold text-foreground mb-3 md:mb-4 truncate">
                {selectedMetrics.size === 1
                  ? availableMetrics.find((m) => selectedMetrics.has(m.xbrlTag))?.label
                  : `${selectedMetrics.size} Metrics Comparison`}
              </h3>
              <ResponsiveContainer width="100%" height={260}>
                <ChartComponent data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                  <XAxis
                    dataKey="year"
                    tick={{ fontSize: 11, fill: 'var(--color-muted-foreground)' }}
                    axisLine={false}
                    tickLine={false}
                  />
                  <YAxis
                    tickFormatter={formatYAxis}
                    tick={{ fontSize: 10, fill: 'var(--color-muted-foreground)' }}
                    axisLine={false}
                    tickLine={false}
                    width={64}
                  />
                  <Tooltip content={<CustomTooltip />} />
                  <Legend wrapperStyle={{ fontSize: 10, color: 'var(--color-muted-foreground)' }} />
                  {seriesKeys.map((key, i) => {
                    const color = METRIC_COLORS[i % METRIC_COLORS.length]
                    if (chartType === 'bar') {
                      return <Bar key={key} dataKey={key} fill={color} radius={[3, 3, 0, 0]} maxBarSize={40} />
                    } else if (chartType === 'line') {
                      return (
                        <Line
                          key={key}
                          type="monotone"
                          dataKey={key}
                          stroke={color}
                          strokeWidth={2}
                          dot={{ r: 3, fill: color }}
                          activeDot={{ r: 5 }}
                        />
                      )
                    } else {
                      return (
                        <Area
                          key={key}
                          type="monotone"
                          dataKey={key}
                          stroke={color}
                          fill={color}
                          fillOpacity={0.12}
                          strokeWidth={2}
                        />
                      )
                    }
                  })}
                </ChartComponent>
              </ResponsiveContainer>
            </div>

            {seriesKeys.length > 1 && (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 md:gap-4">
                {seriesKeys.map((key, i) => {
                  const color = METRIC_COLORS[i % METRIC_COLORS.length]
                  return (
                    <div key={key} className="bg-card border border-border rounded-xl p-3 md:p-4">
                      <h4 className="text-xs font-semibold text-foreground mb-2 md:mb-3 truncate">
                        {key}
                      </h4>
                      <ResponsiveContainer width="100%" height={120}>
                        <AreaChart data={chartData}>
                          <defs>
                            <linearGradient id={`grad-${i}`} x1="0" y1="0" x2="0" y2="1">
                              <stop offset="0%" stopColor={color} stopOpacity={0.3} />
                              <stop offset="100%" stopColor={color} stopOpacity={0.02} />
                            </linearGradient>
                          </defs>
                          <XAxis
                            dataKey="year"
                            tick={{ fontSize: 9, fill: 'var(--color-muted-foreground)' }}
                            axisLine={false}
                            tickLine={false}
                          />
                          <YAxis
                            tickFormatter={formatYAxis}
                            tick={{ fontSize: 9, fill: 'var(--color-muted-foreground)' }}
                            axisLine={false}
                            tickLine={false}
                            width={52}
                          />
                          <Tooltip content={<CustomTooltip />} />
                          <Area
                            type="monotone"
                            dataKey={key}
                            stroke={color}
                            fill={`url(#grad-${i})`}
                            strokeWidth={2}
                          />
                        </AreaChart>
                      </ResponsiveContainer>
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        )}
      </div>

      {mobileControlsOpen && (
        <div
          className="md:hidden fixed inset-0 z-40 bg-black/50"
          onClick={() => setMobileControlsOpen(false)}
        />
      )}

      <div
        className={cn(
          'md:hidden fixed inset-x-0 bottom-0 z-50 flex flex-col bg-background border-t border-border rounded-t-2xl transition-transform duration-300 max-h-[80vh]',
          mobileControlsOpen ? 'translate-y-0' : 'translate-y-full'
        )}
      >
        <div className="flex items-center justify-between px-4 py-3 border-b border-border shrink-0">
          <h2 className="text-sm font-semibold text-foreground">Chart Settings</h2>
          <button
            onClick={() => setMobileControlsOpen(false)}
            className="p-1.5 rounded-md text-muted-foreground hover:text-foreground"
            aria-label="Close settings"
          >
            <X size={18} />
          </button>
        </div>
        <div className="flex-1 overflow-y-auto flex flex-col">
          <ControlsContent {...controlsProps} />
        </div>
      </div>
    </div>
  )
}
