/**
 * CatalogueTabs — filter bar above the shop grid (All / Package / Report).
 * Controlled component: parent owns the active value.
 */
import { cn } from '@/lib/utils'

import type { ProductType } from '@/lib/shop-api'

export type CatalogueTabValue = 'all' | ProductType

export const CATALOGUE_TABS: Array<{ value: CatalogueTabValue; label: string }> = [
  { value: 'all', label: 'Tất cả' },
  { value: 'package', label: 'Gói thuê bao' },
  { value: 'report', label: 'Báo cáo lẻ' },
  { value: 'combo', label: 'Combo ưu đãi' },
]

interface Props {
  value: CatalogueTabValue
  onChange: (value: CatalogueTabValue) => void
}

export default function CatalogueTabs({ value, onChange }: Props) {
  return (
    <div
      role="tablist"
      className="inline-flex flex-wrap items-center gap-1 rounded-xl border border-border bg-card p-1 shadow-sm mb-6"
    >
      {CATALOGUE_TABS.map((t) => {
        const active = t.value === value
        return (
          <button
            key={t.value}
            type="button"
            role="tab"
            aria-selected={active}
            onClick={() => onChange(t.value)}
            className={cn(
              'px-3.5 py-1.5 rounded-lg text-sm font-medium transition-colors',
              'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-1 focus-visible:ring-offset-background',
              active
                ? 'bg-primary text-primary-foreground shadow-sm'
                : 'text-muted-foreground hover:text-foreground hover:bg-muted'
            )}
          >
            {t.label}
          </button>
        )
      })}
    </div>
  )
}
