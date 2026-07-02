import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'
import LanguageDetector from 'i18next-browser-languagedetector'
import en from './locales/en.json'
import fr from './locales/fr.json'
import ja from './locales/ja.json'

export const SUPPORTED_LANGUAGES = ['en', 'fr', 'ja'] as const

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources: {
      en: { translation: en },
      fr: { translation: fr },
      ja: { translation: ja },
    },
    fallbackLng: 'en',
    supportedLngs: SUPPORTED_LANGUAGES,
    interpolation: { escapeValue: false },
  })

export default i18n
