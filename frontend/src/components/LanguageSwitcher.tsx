import { useTranslation } from 'react-i18next'
import { SUPPORTED_LANGUAGES } from '../i18n'

const LABELS: Record<string, string> = { en: 'English', fr: 'Français', ja: '日本語' }

export function LanguageSwitcher() {
  const { i18n, t } = useTranslation()

  return (
    <label className="language-switcher">
      {t('language.label')}:{' '}
      <select
        value={i18n.resolvedLanguage}
        onChange={(e) => i18n.changeLanguage(e.target.value)}
      >
        {SUPPORTED_LANGUAGES.map((lng) => (
          <option key={lng} value={lng}>
            {LABELS[lng]}
          </option>
        ))}
      </select>
    </label>
  )
}
