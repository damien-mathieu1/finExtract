import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Route, Routes } from 'react-router-dom'
import { CompanySearchPage } from './pages/CompanySearchPage'
import { FilingListPage } from './pages/FilingListPage'
import { StatementDetailPage } from './pages/StatementDetailPage'
import { UploadPage } from './pages/UploadPage'
import { HistoryPage } from './pages/HistoryPage'
import { LanguageSwitcher } from './components/LanguageSwitcher'
import './App.css'

const queryClient = new QueryClient()

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <main className="app">
          <div className="app-header">
            <LanguageSwitcher />
          </div>
          <Routes>
            <Route path="/" element={<CompanySearchPage />} />
            <Route path="/companies/:cik/filings" element={<FilingListPage />} />
            <Route path="/extractions/:id" element={<StatementDetailPage />} />
            <Route path="/upload" element={<UploadPage />} />
            <Route path="/history" element={<HistoryPage />} />
          </Routes>
        </main>
      </BrowserRouter>
    </QueryClientProvider>
  )
}

export default App
