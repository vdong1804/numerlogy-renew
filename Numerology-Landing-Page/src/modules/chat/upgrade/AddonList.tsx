/**
 * AddonList — fetches all chat add-on packages and renders a grid of AddonCards.
 * onPurchase: caller handles the actual purchase flow (navigate / inline display).
 */

import { PackageOpen, RefreshCcw } from 'lucide-react'
import { useCallback, useEffect, useState } from 'react'

import type { AddonPackage } from '@/models/Chat'

import { listAddons } from '../api/chat-api'
import AddonCard from './AddonCard'

interface AddonListProps {
  onPurchase: (id: number) => Promise<void>
  purchasingId?: number | null
  /** When set, show only the first `limit` packages sorted by price ascending. */
  limit?: number
}

export default function AddonList({
  onPurchase,
  purchasingId = null,
  limit,
}: AddonListProps) {
  const [packages, setPackages] = useState<AddonPackage[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    try {
      const data = await listAddons()
      setPackages(data)
    } catch (err) {
      setError((err as Error).message || 'Không tải được danh sách gói')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  if (loading) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {[1, 2, 3].map((n) => (
          <div
            key={n}
            className="h-48 rounded-xl border border-border bg-card/40 animate-pulse"
          />
        ))}
      </div>
    )
  }

  if (error) {
    return (
      <div
        role="alert"
        className="rounded-xl border border-destructive/30 bg-destructive/5 px-5 py-6 text-center"
      >
        <p className="text-sm text-destructive font-medium mb-3">{error}</p>
        <button
          type="button"
          onClick={() => {
            setLoading(true)
            setError(null)
            load()
          }}
          className="inline-flex items-center gap-1.5 rounded-full bg-destructive/10 hover:bg-destructive/20 px-3 py-1.5 text-xs text-destructive font-medium transition-colors"
        >
          <RefreshCcw className="w-3 h-3" aria-hidden="true" />
          Thử lại
        </button>
      </div>
    )
  }

  if (packages.length === 0) {
    return (
      <div className="rounded-xl border border-dashed border-border bg-card/40 px-6 py-10 text-center">
        <span
          aria-hidden="true"
          className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-muted text-muted-foreground mb-3"
        >
          <PackageOpen className="w-6 h-6" />
        </span>
        <p className="text-sm font-medium text-foreground mb-1">
          Hiện chưa có gói tin nhắn nào
        </p>
        <p className="text-xs text-muted-foreground max-w-sm mx-auto">
          Các gói nâng cấp đang được chuẩn bị. Vui lòng quay lại sau hoặc liên
          hệ hotline{' '}
          <a
            href="tel:0339387373"
            className="text-primary hover:underline font-medium"
          >
            0339 387 373
          </a>{' '}
          để được tư vấn.
        </p>
      </div>
    )
  }

  // Sort cheapest-first then apply optional limit (M6).
  const sorted = [...packages].sort((a, b) => a.price - b.price)
  const visible = limit !== undefined ? sorted.slice(0, limit) : sorted

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      {visible.map((pkg) => (
        <AddonCard
          key={pkg.id}
          pkg={pkg}
          onPurchase={onPurchase}
          // Show spinner only on the in-flight card; disable all others (M7).
          loading={purchasingId === pkg.id}
          disabled={purchasingId !== null && purchasingId !== pkg.id}
        />
      ))}
    </div>
  )
}
