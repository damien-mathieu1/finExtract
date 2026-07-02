import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { downloadExport } from '../api/extractions'

export function ExportButtons({ extractionId }: { extractionId: number }) {
  const { t } = useTranslation()
  const [error, setError] = useState<string | null>(null)

  const handle = (format: 'csv' | 'excel') => {
    setError(null)
    downloadExport(extractionId, format).catch((e: Error) => setError(e.message))
  }

  return (
    <div className="export-buttons">
      <button onClick={() => handle('csv')}>{t('export.csv')}</button>
      <button onClick={() => handle('excel')}>{t('export.excel')}</button>
      {error && <span className="error">{error}</span>}
    </div>
  )
}
