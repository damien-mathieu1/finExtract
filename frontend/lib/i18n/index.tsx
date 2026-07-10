'use client'

import { createContext, useContext, useEffect, useMemo, useState } from 'react'
import en, { type Dictionary } from './locales/en'
import fr from './locales/fr'
import ja from './locales/ja'

export type Locale = 'en' | 'fr' | 'ja'

export const LOCALES: { id: Locale; label: string }[] = [
  { id: 'en', label: 'English' },
  { id: 'fr', label: 'Français' },
  { id: 'ja', label: '日本語' },
]

const DICTIONARIES: Record<Locale, Dictionary> = { en, fr, ja }
const STORAGE_KEY = 'finextract-locale'

type Vars = Record<string, string | number>

// Dot-path lookup into the dictionary, e.g. "filingSearch.extractPanel.launchExtraction".
function resolve(dict: unknown, path: string): unknown {
  return path.split('.').reduce<unknown>((node, key) => {
    if (node && typeof node === 'object' && key in node) {
      return (node as Record<string, unknown>)[key]
    }
    return undefined
  }, dict)
}

function interpolate(template: string, vars?: Vars): string {
  if (!vars) return template
  return template.replace(/\{\{(\w+)\}\}/g, (_, key) => String(vars[key] ?? ''))
}

interface LocaleContextValue {
  locale: Locale
  setLocale: (locale: Locale) => void
  t: (path: string, vars?: Vars) => string
}

const LocaleContext = createContext<LocaleContextValue | null>(null)

function detectInitialLocale(): Locale {
  if (typeof window === 'undefined') return 'en'
  const stored = window.localStorage.getItem(STORAGE_KEY)
  if (stored === 'en' || stored === 'fr' || stored === 'ja') return stored
  const browser = window.navigator.language.slice(0, 2)
  if (browser === 'fr' || browser === 'ja') return browser
  return 'en'
}

export function LocaleProvider({ children }: { children: React.ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>('en')

  useEffect(() => {
    setLocaleState(detectInitialLocale())
  }, [])

  useEffect(() => {
    document.documentElement.lang = locale
  }, [locale])

  function setLocale(next: Locale) {
    setLocaleState(next)
    window.localStorage.setItem(STORAGE_KEY, next)
  }

  const t = useMemo(() => {
    const dict = DICTIONARIES[locale]
    return (path: string, vars?: Vars) => {
      const value = resolve(dict, path) ?? resolve(en, path)
      if (typeof value !== 'string') return path
      return interpolate(value, vars)
    }
  }, [locale])

  return (
    <LocaleContext.Provider value={{ locale, setLocale, t }}>{children}</LocaleContext.Provider>
  )
}

export function useTranslation() {
  const ctx = useContext(LocaleContext)
  if (!ctx) throw new Error('useTranslation must be used within LocaleProvider')
  return ctx
}
