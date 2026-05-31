/**
 * AddonCard — displays a single chat add-on package with pricing and CTA.
 * Shows strikethrough original price when priceSale < price.
 * Tier badge: "Pro" (blue) | "Flash" (amber).
 */

import { Loader2, Zap } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { cn, formatVnd } from '@/lib/utils'
import type { AddonPackage } from '@/models/Chat'

interface AddonCardProps {
  pkg: AddonPackage
  onPurchase: (id: number) => Promise<void>
  loading?: boolean
  /** When true, disables CTA without showing spinner (another card is in flight). */
  disabled?: boolean
}

const TIER_STYLES: Record<string, string> = {
  pro: 'bg-blue-500/10 text-blue-600 border-blue-500/30',
  flash: 'bg-amber-500/10 text-amber-600 border-amber-500/30',
}

export default function AddonCard({
  pkg,
  onPurchase,
  loading = false,
  disabled = false,
}: AddonCardProps) {
  const hasSale = pkg.priceSale > 0 && pkg.priceSale < pkg.price
  const displayPrice = hasSale ? pkg.priceSale : pkg.price
  const tierStyle = pkg.tier
    ? TIER_STYLES[pkg.tier] ?? TIER_STYLES.flash
    : TIER_STYLES.flash
  const tierLabel = pkg.tier === 'pro' ? 'Pro' : 'Flash'

  return (
    <div className="rounded-xl border border-border bg-card p-4 flex flex-col gap-3 hover:border-primary/40 transition-colors">
      {/* Header: name + tier badge */}
      <div className="flex items-start justify-between gap-2">
        <h3 className="font-semibold text-sm text-foreground leading-tight">
          {pkg.name}
        </h3>
        {pkg.tier && (
          <span
            aria-label={`Cấp độ ${tierLabel}`}
            className={cn(
              'inline-flex items-center gap-1 px-1.5 py-0.5 rounded-full border text-xs font-medium shrink-0',
              tierStyle
            )}
          >
            <Zap className="w-3 h-3" aria-hidden="true" />
            {tierLabel}
          </span>
        )}
      </div>

      {/* Meta: message count + validity */}
      <div className="text-xs text-muted-foreground space-y-0.5">
        {pkg.messageCount != null && (
          <p>{pkg.messageCount.toLocaleString('vi-VN')} tin nhắn</p>
        )}
        {pkg.validityDays != null && <p>Hiệu lực {pkg.validityDays} ngày</p>}
        {pkg.description && (
          <p className="text-muted-foreground/80 line-clamp-2">
            {pkg.description}
          </p>
        )}
      </div>

      {/* Price */}
      <div className="flex items-baseline gap-2">
        <span className="text-lg font-bold text-primary">
          {formatVnd(displayPrice)}
        </span>
        {hasSale && (
          <span className="text-xs text-muted-foreground line-through">
            {formatVnd(pkg.price)}
          </span>
        )}
      </div>

      {/* CTA */}
      <Button
        size="sm"
        disabled={loading || disabled}
        onClick={() => onPurchase(pkg.id)}
        aria-label={`Mua gói ${pkg.name}`}
        className="w-full"
      >
        {loading ? (
          <>
            <Loader2 className="w-3.5 h-3.5 animate-spin" aria-hidden="true" />
            Đang xử lý...
          </>
        ) : (
          'Mua ngay'
        )}
      </Button>
    </div>
  )
}
