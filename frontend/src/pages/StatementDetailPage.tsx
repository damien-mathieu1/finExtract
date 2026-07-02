import { useQuery } from '@tanstack/react-query'
import { Link, useParams } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { getExtraction } from '../api/extractions'
import { LineItemsTable } from '../components/LineItemsTable'
import { ExportButtons } from '../components/ExportButtons'

export function StatementDetailPage() {
  const { t } = useTranslation()
  const { id = '' } = useParams()
  const extractionId = Number(id)

  const { data: statement, isFetching, error } = useQuery({
    queryKey: ['extraction', extractionId],
    queryFn: () => getExtraction(extractionId),
  })

  return (
    <div>
      <p>
        <Link to="/">{t('filings.back')}</Link>
      </p>
      {isFetching && <p>{t('statement.loading')}</p>}
      {error instanceof Error && <p className="error">{error.message}</p>}
      {statement && (
        <>
          <h1>{statement.company_name}</h1>
          <p>
            {statement.period_label} · {statement.currency} · {statement.accounting_standard}
          </p>
          <ExportButtons extractionId={extractionId} />
          <LineItemsTable lineItems={statement.line_items} />
        </>
      )}
    </div>
  )
}
