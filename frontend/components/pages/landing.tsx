'use client'

import Link from 'next/link'
import { ArrowRight, BarChart2, Database, FileText, GitMerge, Globe, Languages } from 'lucide-react'

function GithubIcon({ size = 15 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
      <path d="M12 .5C5.65.5.5 5.65.5 12c0 5.08 3.29 9.39 7.86 10.91.57.1.79-.25.79-.55 0-.27-.01-1.16-.02-2.11-3.2.7-3.87-1.36-3.87-1.36-.52-1.33-1.28-1.68-1.28-1.68-1.04-.72.08-.7.08-.7 1.15.08 1.76 1.19 1.76 1.19 1.03 1.75 2.69 1.25 3.35.96.1-.75.4-1.25.73-1.54-2.55-.29-5.24-1.28-5.24-5.68 0-1.25.44-2.28 1.18-3.08-.12-.29-.51-1.46.11-3.04 0 0 .97-.31 3.17 1.18a10.9 10.9 0 0 1 5.78 0c2.2-1.49 3.17-1.18 3.17-1.18.62 1.58.23 2.75.11 3.04.74.8 1.18 1.83 1.18 3.08 0 4.41-2.69 5.38-5.25 5.67.41.36.78 1.07.78 2.16 0 1.56-.01 2.82-.01 3.2 0 .31.21.66.79.55A11.51 11.51 0 0 0 23.5 12C23.5 5.65 18.35.5 12 .5Z" />
    </svg>
  )
}

function LinkedinIcon({ size = 15 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
      <path d="M20.45 20.45h-3.56v-5.57c0-1.33-.02-3.04-1.85-3.04-1.85 0-2.14 1.45-2.14 2.94v5.67H9.34V9h3.41v1.56h.05c.48-.9 1.64-1.85 3.38-1.85 3.61 0 4.28 2.38 4.28 5.48v6.26ZM5.34 7.43a2.06 2.06 0 1 1 0-4.13 2.06 2.06 0 0 1 0 4.13ZM7.12 20.45H3.56V9h3.56v11.45Z" />
    </svg>
  )
}
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
        <div className="mx-auto max-w-5xl px-4 md:px-6 py-6 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-muted-foreground">
          <div className="flex flex-col sm:flex-row items-center gap-1 sm:gap-2">
            <span>{t('landing.footer.credit', { year: new Date().getFullYear() })}</span>
            <span className="hidden sm:inline">·</span>
            <span>{t('landing.footer.sources')}</span>
          </div>
          <div className="flex items-center gap-3">
            <a
              href="https://github.com/damien-mathieu1/finExtract"
              target="_blank"
              rel="noopener noreferrer"
              title={t('landing.footer.repo')}
              className="flex items-center gap-1.5 hover:text-foreground transition-colors"
            >
              <GithubIcon />
              <span>{t('landing.footer.repo')}</span>
            </a>
            <a
              href="https://github.com/damien-mathieu1"
              target="_blank"
              rel="noopener noreferrer"
              title="GitHub"
              aria-label="GitHub"
              className="hover:text-foreground transition-colors"
            >
              <GithubIcon />
            </a>
            <a
              href="https://www.linkedin.com/in/damien-mathieu1/"
              target="_blank"
              rel="noopener noreferrer"
              title="LinkedIn"
              aria-label="LinkedIn"
              className="hover:text-foreground transition-colors"
            >
              <LinkedinIcon />
            </a>
          </div>
        </div>
      </footer>
    </div>
  )
}
