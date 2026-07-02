import { useTranslation } from 'react-i18next'

const LOW_THRESHOLD = 0.5
const WARN_THRESHOLD = 0.8

export function ConfidenceBadge({ score }: { score: number | null }) {
  const { t } = useTranslation()

  if (score === null) return <span className="confidence confidence-neutral">—</span>

  const level = score < LOW_THRESHOLD ? 'low' : score < WARN_THRESHOLD ? 'warn' : 'ok'
  const label =
    level === 'low'
      ? t('confidence.low')
      : level === 'warn'
        ? t('confidence.medium')
        : t('confidence.high')

  return (
    <span className={`confidence confidence-${level}`} title={label}>
      {score.toFixed(2)}
    </span>
  )
}
