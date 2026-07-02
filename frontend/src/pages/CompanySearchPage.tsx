import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { searchCompanies } from '../api/companies'

export function CompanySearchPage() {
  const { t } = useTranslation()
  const [query, setQuery] = useState('')
  const [submitted, setSubmitted] = useState('')

  const { data, isFetching, error } = useQuery({
    queryKey: ['companies', submitted],
    queryFn: () => searchCompanies(submitted),
    enabled: submitted.length > 0,
  })

  return (
    <div>
      <h1>{t('app.title')}</h1>
      <form
        onSubmit={(e) => {
          e.preventDefault()
          setSubmitted(query.trim())
        }}
      >
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={t('search.placeholder')}
        />
        <button type="submit">{t('search.submit')}</button>
      </form>

      <p>
        {t('search.uploadPrompt')} <Link to="/upload">{t('search.uploadLinkText')}</Link>
        {' · '}
        <Link to="/history">{t('search.historyLinkText')}</Link>
      </p>

      {isFetching && <p>{t('search.searching')}</p>}
      {error instanceof Error && <p className="error">{error.message}</p>}

      <ul className="company-list">
        {data?.map((c) => (
          <li key={c.cik}>
            <Link to={`/companies/${c.cik}/filings`}>
              {c.name} {c.ticker ? `(${c.ticker})` : ''}
            </Link>
          </li>
        ))}
      </ul>
    </div>
  )
}
