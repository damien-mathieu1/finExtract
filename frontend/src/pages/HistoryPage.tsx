import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { listExtractions } from '../api/extractions'

export function HistoryPage() {
  const { t } = useTranslation()
  const { data, isFetching, error } = useQuery({
    queryKey: ['extractions', 'all'],
    queryFn: () => listExtractions({}),
  })

  return (
    <div>
      <p>
        <Link to="/">{t('filings.back')}</Link>
      </p>
      <h1>{t('history.title')}</h1>
      {isFetching && <p>{t('filings.loading')}</p>}
      {error instanceof Error && <p className="error">{error.message}</p>}
      <table>
        <thead>
          <tr>
            <th>{t('history.company')}</th>
            <th>{t('history.period')}</th>
            <th>{t('history.standard')}</th>
            <th>{t('history.source')}</th>
            <th>{t('history.extractedAt')}</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {data?.map((e) => (
            <tr key={e.id}>
              <td>{e.company_name}</td>
              <td>{e.period_label}</td>
              <td>{e.accounting_standard}</td>
              <td>{e.source_reference}</td>
              <td>{new Date(e.extracted_at).toLocaleString()}</td>
              <td>
                <Link to={`/extractions/${e.id}`}>{t('filings.viewExtracted')}</Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {data && data.length === 0 && <p>{t('history.empty')}</p>}
    </div>
  )
}
