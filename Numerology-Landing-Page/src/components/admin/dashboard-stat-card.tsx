/**
 * Stat card with optional trend indicator + accent color.
 */
import * as React from 'react'
import Link from 'next/link'
import { ArrowDownRight, ArrowUpRight, type LucideIcon } from 'lucide-react'

import { Card } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { cn } from '@/lib/utils'

export interface StatCardProps {
  label: string
  value?: number | string
  href?: string
  icon: LucideIcon
  /** Accent color class for icon background (e.g. 'bg-primary/10 text-primary'). */
  accentClassName?: string
  /** Optional change percentage (positive = up, negative = down) */
  trend?: number
  trendLabel?: string
  loading?: boolean
}

export function DashboardStatCard({
  label,
  value,
  href,
  icon: Icon,
  accentClassName = 'bg-primary/10 text-primary',
  trend,
  trendLabel,
  loading,
}: StatCardProps) {
  const inner = (
    <Card
      className={cn(
        'admin-card-hover group relative overflow-hidden p-5 border-border/80',
        href && 'cursor-pointer'
      )}
    >
      <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-primary/40 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
      <div className="flex items-start justify-between">
        <div className={cn('flex items-center justify-center w-10 h-10 rounded-lg', accentClassName)}>
          <Icon className="w-5 h-5" />
        </div>
        {typeof trend === 'number' && (
          <span
            className={cn(
              'inline-flex items-center gap-1 text-xs font-semibold px-2 py-0.5 rounded-full',
              trend >= 0
                ? 'bg-success/15 text-success'
                : 'bg-destructive/15 text-destructive'
            )}
          >
            {trend >= 0 ? <ArrowUpRight className="w-3 h-3" /> : <ArrowDownRight className="w-3 h-3" />}
            {Math.abs(trend).toFixed(1)}%
          </span>
        )}
      </div>

      <div className="mt-4">
        <p className="text-xs uppercase tracking-wide text-muted-foreground font-medium">{label}</p>
        {loading ? (
          <Skeleton className="h-9 w-20 mt-1.5" />
        ) : (
          <p className="mt-1 text-3xl font-bold tracking-tight">{value ?? '—'}</p>
        )}
        {trendLabel && (
          <p className="mt-1 text-xs text-muted-foreground">{trendLabel}</p>
        )}
      </div>
    </Card>
  )

  return href ? <Link href={href}>{inner}</Link> : inner
}
