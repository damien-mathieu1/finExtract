import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { listFilings } from '../api/companies'
import { listExtractions, processFiling } from '../api/extractions'
import type { FilingSummaryResponse } from '../api/types'

function FilingRow({ filing }: { filing: FilingSummaryResponse }) {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const { data: existing } = useQuery({
    queryKey: ['extractions', 'by-source', filing.document_url],
    queryFn: () => listExtractions({ sourceReference: filing.document_url }),
  })

  const extractMutation = useMutation({
    mutationFn: () => processFiling(filing.document_url, 'json'),
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: ['extractions', 'by-source', filing.document_url],
      })
      const [fresh] = await listExtractions({ sourceReference: filing.document_url })
      if (fresh) navigate(`/extractions/${fresh.id}`)
    },
  })

  const extraction = existing?.[0]

  return (
    <tr>
      <td>{filing.form_type}</td>
      <td>{filing.filing_date}</td>
      <td>{filing.accession_number}</td>
      <td>
        {extraction ? (
          <Link to={`/extractions/${extraction.id}`}>{t('filings.viewExtracted')}</Link>
        ) : (
          <button onClick={() => extractMutation.mutate()} disabled={extractMutation.isPending}>
            {extractMutation.isPending ? t('filings.extracting') : t('filings.extract')}
          </button>
        )}
        {extractMutation.isError && <span className="error"> {(extractMutation.error as Error).message}</span>}
      </td>
    </tr>
  )
}

export function FilingListPage() {
  const { t } = useTranslation()
  const { cik = '' } = useParams()
  const { data, isFetching, error } = useQuery({
    queryKey: ['filings', cik],
    queryFn: () => listFilings(cik),
  })

  return (
    <div>
      <p>
        <Link to="/">{t('filings.back')}</Link>
      </p>
      <h1>{t('filings.title')}</h1>
      {isFetching && <p>{t('filings.loading')}</p>}
      {error instanceof Error && <p className="error">{error.message}</p>}
      <table>
        <thead>
          <tr>
            <th>{t('filings.form')}</th>
            <th>{t('filings.filed')}</th>
            <th>{t('filings.accession')}</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {data?.map((f) => (
            <FilingRow key={f.accession_number} filing={f} />
          ))}
        </tbody>
      </table>
    </div>
  )
}
