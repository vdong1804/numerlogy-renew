/**
 * Standardized page header for admin list/detail pages.
 */
import * as React from 'react'
import Link from 'next/link'
import { AlertCircle, ChevronLeft, Plus } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

interface AdminPageHeaderProps {
  title: string
  description?: string
  /** Show back-link button on the left of the title */
  backHref?: string
  /** Primary action (e.g. "+ Tạo mới"). */
  primaryAction?: {
    href?: string
    label: string
    onClick?: () => void
    icon?: React.ReactNode
  }
  children?: React.ReactNode
}

export function AdminPageHeader({
  title,
  description,
  backHref,
  primaryAction,
  children,
}: AdminPageHeaderProps) {
  return (
    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-6">
      <div className="flex items-start gap-3">
        {backHref && (
          <Link
            href={backHref}
            className="mt-1 flex items-center justify-center w-8 h-8 rounded-lg border border-border bg-card hover:bg-accent/60 transition-colors"
            aria-label="Quay lại"
          >
            <ChevronLeft className="w-4 h-4" />
          </Link>
        )}
        <div>
          <h1 className="text-2xl font-bold tracking-tight">{title}</h1>
          {description && (
            <p className="mt-1 text-sm text-muted-foreground">{description}</p>
          )}
        </div>
      </div>
      <div className="flex items-center gap-2">
        {children}
        {primaryAction &&
          (primaryAction.href ? (
            <Button asChild variant="default" size="default">
              <Link href={primaryAction.href}>
                {primaryAction.icon ?? <Plus className="w-4 h-4" />}
                {primaryAction.label}
              </Link>
            </Button>
          ) : (
            <Button onClick={primaryAction.onClick}>
              {primaryAction.icon ?? <Plus className="w-4 h-4" />}
              {primaryAction.label}
            </Button>
          ))}
      </div>
    </div>
  )
}

interface ErrorBannerProps {
  message?: string | null
  className?: string
}

export function ErrorBanner({ message, className }: ErrorBannerProps) {
  if (!message) return null
  return (
    <div
      className={cn(
        'flex items-start gap-2 rounded-md border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive mb-4',
        className
      )}
    >
      <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
      <span>{message}</span>
    </div>
  )
}
