/**
 * AddonList — fetches all chat add-on packages and renders a grid of AddonCards.
 * onPurchase: caller handles the actual purchase flow (navigate / inline display).
 */

import { Loader2 } from 'lucide-react'
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
      <div className="flex items-center justify-center py-12 text-muted-foreground">
        <Loader2 className="w-5 h-5 animate-spin mr-2" aria-hidden="true" />
        <span className="text-sm">Đang tải gói tin nhắn...</span>
      </div>
    )
  }

  if (error) {
    return (
      <p role="alert" className="text-sm text-destructive text-center py-8">
        {error}
      </p>
    )
  }

  if (packages.length === 0) {
    return (
      <p className="text-sm text-muted-foreground text-center py-8">
        Chưa có gói tin nhắn nào.
      </p>
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
