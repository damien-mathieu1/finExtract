'use client'

import { UserButton } from '@clerk/nextjs'
import { cn } from '@/lib/utils'
import { useTranslation } from '@/lib/i18n'
import { LanguageSwitcher } from '@/components/language-switcher'
import {
  Search,
  Database,
  BarChart2,
  FileText,
  GitMerge,
  ChevronLeft,
  ChevronRight,
  X,
  Menu,
} from 'lucide-react'
import { useState, useEffect } from 'react'

export type AppPage = 'search' | 'extractions' | 'viewer' | 'charts'
export type ViewerSelection = number[]

interface NavItem {
  id: AppPage
  icon: React.ReactNode
}

const NAV_ITEMS: NavItem[] = [
  { id: 'search', icon: <Search size={18} /> },
  { id: 'extractions', icon: <Database size={18} /> },
  { id: 'viewer', icon: <FileText size={18} /> },
  { id: 'charts', icon: <BarChart2 size={18} /> },
]

const NAV_KEY: Record<AppPage, string> = {
  search: 'search',
  extractions: 'extractions',
  viewer: 'viewer',
  charts: 'charts',
}

interface AppSidebarProps {
  activePage: AppPage
  onNavigate: (page: AppPage) => void
  extractionCount: number
}

export function AppSidebar({ activePage, onNavigate, extractionCount }: AppSidebarProps) {
  const { t } = useTranslation()
  const [collapsed, setCollapsed] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)

  // Close mobile drawer on resize to desktop
  useEffect(() => {
    function onResize() {
      if (window.innerWidth >= 768) setMobileOpen(false)
    }
    window.addEventListener('resize', onResize)
    return () => window.removeEventListener('resize', onResize)
  }, [])

  function handleNavigate(page: AppPage) {
    onNavigate(page)
    setMobileOpen(false)
  }

  const NavContent = (
    <>
      {/* Logo */}
      <div
        className={cn(
          'flex items-center gap-3 px-4 py-5 border-b border-sidebar-border',
          collapsed && 'justify-center px-0'
        )}
      >
        <div className="flex items-center justify-center w-8 h-8 rounded-md bg-primary shrink-0">
          <GitMerge size={16} className="text-primary-foreground" />
        </div>
        {!collapsed && (
          <div>
            <span className="text-sm font-semibold text-sidebar-foreground tracking-tight">
              {t('app.name')}
            </span>
            <p className="text-[10px] text-sidebar-foreground/50 leading-none mt-0.5">
              {t('app.tagline')}
            </p>
          </div>
        )}
        {/* Mobile close button */}
        <button
          onClick={() => setMobileOpen(false)}
          className="ml-auto md:hidden p-1 text-sidebar-foreground/50 hover:text-sidebar-foreground"
          aria-label={t('sidebar.closeMenu')}
        >
          <X size={18} />
        </button>
      </div>

      {/* Nav */}
      <nav className="flex-1 py-4 space-y-1 px-2">
        {NAV_ITEMS.map((item) => {
          const label = t(`sidebar.nav.${NAV_KEY[item.id]}.label`)
          const description = t(`sidebar.nav.${NAV_KEY[item.id]}.description`)
          return (
            <button
              key={item.id}
              onClick={() => handleNavigate(item.id)}
              className={cn(
                'w-full flex items-center gap-3 rounded-md px-3 py-3 text-left transition-colors',
                activePage === item.id
                  ? 'bg-sidebar-primary text-sidebar-primary-foreground'
                  : 'text-sidebar-foreground/70 hover:bg-sidebar-accent hover:text-sidebar-accent-foreground',
                collapsed && 'justify-center px-0'
              )}
              title={collapsed ? label : undefined}
            >
              <span className="shrink-0">{item.icon}</span>
              {!collapsed && (
                <div className="min-w-0 flex-1">
                  <div className="text-sm font-medium leading-none">{label}</div>
                  <div className="text-[11px] mt-1 opacity-60 truncate">{description}</div>
                </div>
              )}
              {!collapsed && item.id === 'extractions' && extractionCount > 0 && (
                <span className="shrink-0 text-[10px] font-semibold bg-primary/20 text-primary rounded-full px-1.5 py-0.5">
                  {extractionCount}
                </span>
              )}
            </button>
          )
        })}
      </nav>

      <LanguageSwitcher collapsed={collapsed} />

      <div className={cn('flex items-center px-3 py-2', collapsed && 'justify-center px-0')}>
        <UserButton />
      </div>

      {/* Desktop collapse toggle */}
      <button
        onClick={() => setCollapsed(!collapsed)}
        className="hidden md:flex items-center justify-center h-10 mt-2 border-t border-sidebar-border text-sidebar-foreground/40 hover:text-sidebar-foreground/80 transition-colors"
      >
        {collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
      </button>
    </>
  )

  return (
    <>
      {/* Mobile top bar */}
      <div className="md:hidden flex items-center justify-between px-4 py-3 bg-sidebar border-b border-sidebar-border shrink-0">
        <div className="flex items-center gap-2">
          <div className="flex items-center justify-center w-7 h-7 rounded-md bg-primary shrink-0">
            <GitMerge size={14} className="text-primary-foreground" />
          </div>
          <span className="text-sm font-semibold text-sidebar-foreground tracking-tight">
            {t('app.name')}
          </span>
        </div>
        <div className="flex items-center gap-3">
          {extractionCount > 0 && (
            <span className="text-[10px] font-semibold bg-primary/20 text-primary rounded-full px-2 py-0.5">
              {t('sidebar.extractionsBadge', { count: extractionCount })}
            </span>
          )}
          <button
            onClick={() => setMobileOpen(true)}
            className="p-1.5 rounded-md text-sidebar-foreground/70 hover:text-sidebar-foreground hover:bg-sidebar-accent"
            aria-label={t('sidebar.openMenu')}
          >
            <Menu size={20} />
          </button>
        </div>
      </div>

      {/* Mobile overlay */}
      {mobileOpen && (
        <div
          className="md:hidden fixed inset-0 z-40 bg-black/50"
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* Mobile slide-over drawer */}
      <aside
        className={cn(
          'md:hidden fixed inset-y-0 left-0 z-50 w-72 flex flex-col bg-sidebar text-sidebar-foreground transition-transform duration-250',
          mobileOpen ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        {NavContent}
      </aside>

      {/* Desktop sidebar */}
      <aside
        className={cn(
          'hidden md:flex flex-col bg-sidebar text-sidebar-foreground border-r border-sidebar-border transition-all duration-200 shrink-0',
          collapsed ? 'w-16' : 'w-60'
        )}
      >
        {NavContent}
      </aside>
    </>
  )
}
