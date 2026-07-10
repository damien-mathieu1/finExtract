'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { AppSidebar, type AppPage } from '@/components/app-sidebar'
import { FilingSearchPage } from '@/components/pages/filing-search'
import { ExtractionsPage } from '@/components/pages/extractions'
import { DataViewerPage } from '@/components/pages/data-viewer'
import { ChartsPage } from '@/components/pages/charts'
import { listExtractions } from '@/lib/api/extractions'
import { Toaster } from '@/components/ui/sonner'

export default function Page() {
  const [activePage, setActivePage] = useState<AppPage>('search')
  const [viewerIds, setViewerIds] = useState<number[]>([])
  const { data: extractions = [] } = useQuery({
    queryKey: ['extractions'],
    queryFn: () => listExtractions({}),
  })

  function handleNavigate(page: AppPage, selectedIds?: number[]) {
    if (page === 'viewer' && selectedIds) {
      setViewerIds(selectedIds)
    }
    setActivePage(page)
  }

  return (
    <div className="flex flex-col md:flex-row h-svh overflow-hidden bg-background">
      <AppSidebar
        activePage={activePage}
        onNavigate={(page) => setActivePage(page)}
        extractionCount={extractions.length}
      />
      <main className="flex-1 min-w-0 overflow-hidden flex flex-col">
        {activePage === 'search' && <FilingSearchPage onNavigate={handleNavigate} />}
        {activePage === 'extractions' && <ExtractionsPage onNavigate={handleNavigate} />}
        {activePage === 'viewer' && (
          <DataViewerPage selectedExtractionIds={viewerIds} onNavigate={setActivePage} />
        )}
        {activePage === 'charts' && <ChartsPage />}
      </main>
      <Toaster position="bottom-center" />
    </div>
  )
}
