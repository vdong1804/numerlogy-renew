/**
 * ProductCard — single tile in the shop catalogue grid.
 * Click navigates to /shop/[slug].
 */
import Link from 'next/link'
import { ArrowRight, Calendar, FileText, Layers, Package } from 'lucide-react'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { formatVnd } from '@/lib/utils'

import type { Product } from '@/lib/shop-api'

const TYPE_LABEL: Record<Product['type'], string> = {
  package: 'Gói thuê bao',
  report: 'Báo cáo lẻ',
  combo: 'Combo',
}

const TYPE_ICON: Record<Product['type'], typeof Package> = {
  package: Package,
  report: FileText,
  combo: Layers,
}

interface Props {
  product: Product
}

export default function ProductCard({ product }: Props) {
  const free = product.price === 0
  const TypeIcon = TYPE_ICON[product.type]
  return (
    <div
      className="group flex flex-col rounded-2xl border border-border bg-card overflow-hidden
                 shadow-sm transition-all hover:border-primary/50 hover:shadow-lg hover:-translate-y-1"
    >
      {/* Header strip with type label + free badge */}
      <div className="flex items-center justify-between gap-2 border-b border-border bg-gradient-to-r from-primary/8 via-muted/30 to-secondary/10 px-4 py-2.5">
        <span className="inline-flex items-center gap-1.5 text-xs font-medium text-muted-foreground">
          <TypeIcon className="w-3.5 h-3.5" />
          {TYPE_LABEL[product.type]}
        </span>
        {free ? (
          <Badge className="bg-success text-success-foreground">Miễn phí</Badge>
        ) : product.type === 'combo' ? (
          <Badge variant="outline" className="border-primary/40 text-primary">
            Ưu đãi
          </Badge>
        ) : null}
      </div>

      {/* Body */}
      <div className="flex-1 flex flex-col p-5">
        <h3 className="text-base sm:text-lg font-semibold text-foreground leading-tight" style={{ fontFamily: 'var(--philosopher-font)' }}>
          {product.name}
        </h3>
        {product.description && (
          <p className="text-sm text-muted-foreground line-clamp-3 mt-2">
            {product.description}
          </p>
        )}

        {/* Meta (quota / renewal) */}
        {product.type === 'package' && product.quota != null && (
          <div className="flex flex-wrap items-center gap-x-3 gap-y-1 mt-3 text-xs text-muted-foreground">
            <span className="inline-flex items-center gap-1">
              <FileText className="w-3.5 h-3.5" />
              {product.quota} báo cáo
            </span>
            {product.renewal_days ? (
              <span className="inline-flex items-center gap-1">
                <Calendar className="w-3.5 h-3.5" />
                {product.renewal_days} ngày
              </span>
            ) : null}
          </div>
        )}

        {/* Price + CTA */}
        <div className="mt-auto pt-5 flex items-end justify-between gap-3">
          <div className="leading-none">
            <span className="text-2xl font-bold text-foreground">
              {free ? 'Miễn phí' : formatVnd(product.price)}
            </span>
            {!free && product.type === 'package' && (
              <span className="block text-xs text-muted-foreground mt-1">
                / chu kỳ
              </span>
            )}
          </div>
          <Button asChild size="sm" className="shrink-0">
            <Link href={`/shop/${product.slug}`}>
              Xem chi tiết
              <ArrowRight className="w-3.5 h-3.5 transition-transform group-hover:translate-x-0.5" />
            </Link>
          </Button>
        </div>
      </div>
    </div>
  )
}
