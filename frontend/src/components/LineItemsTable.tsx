import { useTranslation } from 'react-i18next'
import type { LineItemResponse } from '../api/types'
import { ConfidenceBadge } from './ConfidenceBadge'

export function LineItemsTable({ lineItems }: { lineItems: LineItemResponse[] }) {
  const { t } = useTranslation()

  return (
    <table className="line-items-table">
      <thead>
        <tr>
          <th>{t('table.field')}</th>
          <th>{t('table.value')}</th>
          <th>{t('table.originalLabel')}</th>
          <th>{t('table.source')}</th>
          <th>{t('table.page')}</th>
          <th>{t('table.confidence')}</th>
        </tr>
      </thead>
      <tbody>
        {lineItems.map((li) => (
          <tr key={li.field_name} className={li.confidence_score !== null && li.confidence_score < 0.5 ? 'row-low-confidence' : ''}>
            <td>{li.field_name}</td>
            <td>{li.value === null ? '—' : li.value.toLocaleString()}</td>
            <td>{li.original_label}</td>
            <td>{li.source}</td>
            <td>{li.page_number ?? '—'}</td>
            <td>
              <ConfidenceBadge score={li.confidence_score} />
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}
