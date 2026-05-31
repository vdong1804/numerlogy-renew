/**
 * Admin sidebar nav — desktop + mobile (Sheet).
 * Collapsible groups, icons, active states. Uses ADMIN_NAV_GROUPS.
 */
import * as React from 'react'
import Link from 'next/link'
import { useRouter } from 'next/router'
import { ChevronRight, Sparkles } from 'lucide-react'

import { cn } from '@/lib/utils'
import {
  ADMIN_DASHBOARD_ICON,
  ADMIN_DASHBOARD_ITEM,
  ADMIN_NAV_GROUPS,
} from './admin-nav-config'

interface AdminSidebarNavProps {
  onNavigate?: () => void
}

export function AdminSidebarNav({ onNavigate }: AdminSidebarNavProps) {
  const router = useRouter()
  const pathname = router.pathname

  const isActive = (href: string) => {
    if (href === '/admin') return pathname === '/admin'
    return pathname === href || pathname.startsWith(`${href}/`)
  }

  return (
    <div className="flex h-full flex-col bg-card/60 backdrop-blur-sm border-r border-border">
      {/* Brand */}
      <div className="flex items-center gap-3 px-5 h-16 border-b border-border">
        <div className="flex items-center justify-center w-9 h-9 rounded-lg bg-gradient-to-br from-primary to-accent-foreground/80 text-primary-foreground shadow-md">
          <Sparkles className="w-4 h-4" />
        </div>
        <div className="flex flex-col">
          <span className="text-sm font-semibold leading-tight">Numerology</span>
          <span className="text-[11px] text-muted-foreground leading-tight">Admin Console</span>
        </div>
      </div>

      {/* Scrollable nav */}
      <nav className="flex-1 overflow-y-auto p-3 space-y-1">
        <SidebarLink
          href={ADMIN_DASHBOARD_ITEM.href}
          label={ADMIN_DASHBOARD_ITEM.label}
          icon={ADMIN_DASHBOARD_ICON}
          active={pathname === '/admin'}
          onNavigate={onNavigate}
        />

        <div className="my-2 border-t border-border/60" />

        {ADMIN_NAV_GROUPS.map((group) => {
          const first = group.items[0]
          if (group.collapsible && group.items.length > 1) {
            return (
              <CollapsibleGroup
                key={group.id}
                group={group}
                isActive={isActive}
                defaultOpen={group.items.some((i) => isActive(i.href))}
                onNavigate={onNavigate}
              />
            )
          }
          if (!first) return null
          return (
            <SidebarLink
              key={group.id}
              href={first.href}
              label={group.label}
              icon={group.icon}
              active={isActive(first.href)}
              onNavigate={onNavigate}
            />
          )
        })}
      </nav>

      {/* Footer */}
      <div className="px-4 py-3 border-t border-border bg-muted/30">
        <p className="text-[11px] text-muted-foreground">
          v1.0 · <kbd className="px-1.5 py-0.5 rounded bg-muted text-[10px] font-mono">Ctrl K</kbd> để mở lệnh nhanh
        </p>
      </div>
    </div>
  )
}

interface SidebarLinkProps {
  href: string
  label: string
  icon: React.ComponentType<{ className?: string }>
  active: boolean
  indent?: boolean
  onNavigate?: () => void
}

function SidebarLink({ href, label, icon: Icon, active, indent, onNavigate }: SidebarLinkProps) {
  return (
    <Link
      href={href}
      onClick={onNavigate}
      className={cn(
        'group flex items-center gap-2.5 rounded-lg px-2.5 py-2 text-sm font-medium transition-colors',
        indent && 'pl-9',
        active
          ? 'bg-primary/10 text-primary'
          : 'text-foreground/75 hover:text-foreground hover:bg-accent/60'
      )}
    >
      <Icon className={cn('w-4 h-4 shrink-0', active ? 'text-primary' : 'text-muted-foreground group-hover:text-foreground')} />
      <span className="truncate">{label}</span>
      {active && <span className="ml-auto w-1.5 h-1.5 rounded-full bg-primary" />}
    </Link>
  )
}

interface CollapsibleGroupProps {
  group: typeof ADMIN_NAV_GROUPS[number]
  isActive: (href: string) => boolean
  defaultOpen: boolean
  onNavigate?: () => void
}

function CollapsibleGroup({ group, isActive, defaultOpen, onNavigate }: CollapsibleGroupProps) {
  const [open, setOpen] = React.useState(defaultOpen)
  const Icon = group.icon
  const groupActive = group.items.some((i) => isActive(i.href))

  return (
    <div>
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className={cn(
          'group w-full flex items-center gap-2.5 rounded-lg px-2.5 py-2 text-sm font-medium transition-colors',
          groupActive ? 'text-foreground' : 'text-foreground/75 hover:text-foreground hover:bg-accent/60'
        )}
      >
        <Icon className={cn('w-4 h-4 shrink-0', groupActive ? 'text-primary' : 'text-muted-foreground')} />
        <span className="truncate">{group.label}</span>
        <ChevronRight
          className={cn(
            'ml-auto w-3.5 h-3.5 text-muted-foreground transition-transform',
            open && 'rotate-90'
          )}
        />
      </button>
      {open && (
        <div className="mt-1 ml-1 pl-3 border-l border-border/70 space-y-0.5">
          {group.items.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              onClick={onNavigate}
              className={cn(
                'flex items-center gap-2 rounded-md pl-3 pr-2 py-1.5 text-xs transition-colors',
                isActive(item.href)
                  ? 'bg-primary/10 text-primary font-semibold'
                  : 'text-muted-foreground hover:text-foreground hover:bg-accent/40'
              )}
            >
              <span className="truncate">{item.label}</span>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}
