'use client'

import { Languages } from 'lucide-react'
import { LOCALES, useTranslation } from '@/lib/i18n'
import { cn } from '@/lib/utils'

export function LanguageSwitcher({ collapsed = false }: { collapsed?: boolean }) {
  const { locale, setLocale, t } = useTranslation()

  return (
    <div className={cn('flex items-center gap-2 px-2', collapsed && 'justify-center px-0')}>
      <Languages size={14} className="text-sidebar-foreground/50 shrink-0" />
      <select
        value={locale}
        onChange={(e) => setLocale(e.target.value as (typeof LOCALES)[number]['id'])}
        aria-label={t('languageSwitcher.label')}
        className={cn(
          'bg-transparent text-xs text-sidebar-foreground/70 hover:text-sidebar-foreground outline-none cursor-pointer',
          collapsed && 'sr-only'
        )}
      >
        {LOCALES.map((l) => (
          <option key={l.id} value={l.id} className="text-foreground bg-background">
            {l.label}
          </option>
        ))}
      </select>
    </div>
  )
}
