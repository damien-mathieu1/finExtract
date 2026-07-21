'use client'

import { Show } from '@clerk/nextjs'
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { AppSidebar, type AppPage } from '@/components/app-sidebar'
import { FilingSearchPage } from '@/components/pages/filing-search'
import { ExtractionsPage } from '@/components/pages/extractions'
import { DataViewerPage } from '@/components/pages/data-viewer'
import { ChartsPage } from '@/components/pages/charts'
import { LandingPage } from '@/components/pages/landing'
import { listExtractions } from '@/lib/api/extractions'
import { Toaster } from '@/components/ui/sonner'

// The app lives in its own component so its queries only mount for
// signed-in users; signed-out visitors get the public landing page.
function AppShell() {
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

export default function Page() {
  return (
    <>
      <Show when="signed-out">
        <LandingPage />
      </Show>
      <Show when="signed-in">
        <AppShell />
      </Show>
    </>
  )
}
