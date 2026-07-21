'use client'

import Link from 'next/link'
import {
  ArrowRight,
  BarChart2,
  Database,
  FileText,
  GitMerge,
  Globe,
  Languages,
} from 'lucide-react'
import { LOCALES, useTranslation } from '@/lib/i18n'

const FEATURES = [
  { key: 'sources', icon: <Globe size={20} /> },
  { key: 'extraction', icon: <FileText size={20} /> },
  { key: 'normalization', icon: <Database size={20} /> },
  { key: 'export', icon: <BarChart2 size={20} /> },
] as const

export function LandingPage() {
  const { locale, setLocale, t } = useTranslation()

  return (
    <div className="min-h-svh bg-background text-foreground flex flex-col">
      {/* Header */}
      <header className="border-b border-border">
        <div className="mx-auto max-w-5xl px-4 md:px-6 h-14 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="flex items-center justify-center w-7 h-7 rounded-md bg-primary shrink-0">
              <GitMerge size={14} className="text-primary-foreground" />
            </div>
            <span className="text-sm font-semibold tracking-tight">{t('app.name')}</span>
            <span className="hidden sm:inline text-xs text-muted-foreground">
              {t('app.tagline')}
            </span>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-1.5">
              <Languages size={14} className="text-muted-foreground" />
              <select
                value={locale}
                onChange={(e) => setLocale(e.target.value as (typeof LOCALES)[number]['id'])}
                aria-label={t('languageSwitcher.label')}
                className="bg-transparent text-xs text-muted-foreground hover:text-foreground outline-none cursor-pointer"
              >
                {LOCALES.map((l) => (
                  <option key={l.id} value={l.id} className="text-foreground bg-background">
                    {l.label}
                  </option>
                ))}
              </select>
            </div>
            <Link
              href="/sign-in"
              className="text-sm font-medium rounded-md border border-border px-3 py-1.5 hover:bg-accent hover:text-accent-foreground transition-colors"
            >
              {t('landing.nav.signIn')}
            </Link>
          </div>
        </div>
      </header>

      <main className="flex-1">
        {/* Hero */}
        <section className="mx-auto max-w-5xl px-4 md:px-6 pt-16 pb-14 md:pt-24 md:pb-20 text-center">
          <span className="inline-block text-[11px] font-semibold tracking-wide text-primary bg-primary/10 rounded-full px-3 py-1 mb-5">
            {t('landing.hero.badge')}
          </span>
          <h1 className="text-3xl md:text-5xl font-semibold tracking-tight text-balance max-w-3xl mx-auto">
            {t('landing.hero.title')}
          </h1>
          <p className="mt-5 text-base md:text-lg text-muted-foreground max-w-2xl mx-auto text-pretty">
            {t('landing.hero.subtitle')}
          </p>
          <div className="mt-8 flex flex-col items-center gap-2">
            <Link
              href="/sign-in"
              className="inline-flex items-center gap-2 rounded-md bg-primary text-primary-foreground px-5 py-2.5 text-sm font-medium hover:opacity-90 transition-opacity"
            >
              {t('landing.hero.cta')}
              <ArrowRight size={16} />
            </Link>
            <span className="text-xs text-muted-foreground">{t('landing.hero.ctaHint')}</span>
          </div>
        </section>

        {/* Features */}
        <section className="border-t border-border bg-muted/30">
          <div className="mx-auto max-w-5xl px-4 md:px-6 py-14 md:py-16">
            <h2 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground mb-8">
              {t('landing.features.title')}
            </h2>
            <div className="grid sm:grid-cols-2 gap-4">
              {FEATURES.map((f) => (
                <div key={f.key} className="rounded-lg border border-border bg-background p-5">
                  <div className="flex items-center justify-center w-9 h-9 rounded-md bg-primary/10 text-primary mb-3">
                    {f.icon}
                  </div>
                  <h3 className="text-sm font-semibold mb-1.5">
                    {t(`landing.features.${f.key}.title`)}
                  </h3>
                  <p className="text-sm text-muted-foreground leading-relaxed">
                    {t(`landing.features.${f.key}.description`)}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* About */}
        <section className="border-t border-border">
          <div className="mx-auto max-w-3xl px-4 md:px-6 py-14 md:py-16 text-center">
            <h2 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground mb-5">
              {t('landing.about.title')}
            </h2>
            <p className="text-base md:text-lg leading-relaxed text-pretty">
              {t('landing.about.body')}
            </p>
            <p className="mt-4 text-sm md:text-base text-muted-foreground leading-relaxed text-pretty">
              {t('landing.about.goal')}
            </p>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t border-border">
        <div className="mx-auto max-w-5xl px-4 md:px-6 py-6 flex flex-col sm:flex-row items-center justify-between gap-2 text-xs text-muted-foreground">
          <span>{t('landing.footer.credit', { year: new Date().getFullYear() })}</span>
          <span>{t('landing.footer.sources')}</span>
        </div>
      </footer>
    </div>
  )
}
