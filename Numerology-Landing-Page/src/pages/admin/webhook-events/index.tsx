/**
 * Admin webhook events log — /admin/webhook-events
 */
import { useCallback, useEffect, useState } from 'react'

import AdminLayout from '@/components/admin/admin-layout'
import { AdminPageHeader, ErrorBanner } from '@/components/admin/admin-page-header'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import {
  listAdminWebhookEvents,
  type AdminWebhookEvent,
} from '@/lib/admin-dashboard-api'

const PAGE_SIZE = 30
const STATUSES = ['', 'received', 'matched', 'unmatched', 'duplicate', 'amount_mismatch', 'error']

export default function AdminWebhookEventsPage() {
  const [items, setItems] = useState<AdminWebhookEvent[]>([])
  const [pageIndex, setPageIndex] = useState(0)
  const [statusFilter, setStatusFilter] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [expandedId, setExpandedId] = useState<number | null>(null)

  const fetchData = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const res = await listAdminWebhookEvents({
        limit: PAGE_SIZE,
        offset: pageIndex * PAGE_SIZE,
        status: statusFilter || undefined,
      })
      setItems(res.items)
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setLoading(false)
    }
  }, [pageIndex, statusFilter])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  return (
    <AdminLayout title="Webhook Events">
      <AdminPageHeader title="Webhook Events" description="Log SePay và provider khác" />
      <div className="flex gap-2 flex-wrap mb-3">
        {STATUSES.map((s) => (
          <Button
            key={s || 'all'}
            size="sm"
            variant={statusFilter === s ? 'default' : 'outline'}
            onClick={() => {
              setStatusFilter(s)
              setPageIndex(0)
            }}
          >
            {s || 'Tất cả'}
          </Button>
        ))}
      </div>
      <ErrorBanner message={error} />

      {loading ? (
        <Skeleton className="h-64 w-full" />
      ) : (
        <div className="rounded-xl border border-border overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-muted/40 text-left text-xs">
              <tr>
                <th className="px-3 py-2">ID</th>
                <th className="px-3 py-2">Provider</th>
                <th className="px-3 py-2">TX ID</th>
                <th className="px-3 py-2">Status</th>
                <th className="px-3 py-2">Ref</th>
                <th className="px-3 py-2 text-right">Amount</th>
                <th className="px-3 py-2">Lúc</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {items.map((ev) => (
                <>
                  <tr
                    key={ev.id}
                    className="hover:bg-muted/30 cursor-pointer"
                    onClick={() => setExpandedId(expandedId === ev.id ? null : ev.id)}
                  >
                    <td className="px-3 py-2">{ev.id}</td>
                    <td className="px-3 py-2">{ev.provider}</td>
                    <td className="px-3 py-2 font-mono text-xs">{ev.sepay_tx_id}</td>
                    <td className="px-3 py-2">
                      <Badge variant={ev.status === 'matched' ? 'default' : 'outline'}>
                        {ev.status}
                      </Badge>
                    </td>
                    <td className="px-3 py-2 font-mono text-xs">{ev.ref_code ?? '—'}</td>
                    <td className="px-3 py-2 text-right">{ev.amount ?? '—'}</td>
                    <td className="px-3 py-2 text-xs text-muted-foreground">
                      {ev.created_at ? new Date(ev.created_at).toLocaleString('vi-VN') : '—'}
                    </td>
                  </tr>
                  {expandedId === ev.id && (
                    <tr key={`${ev.id}-detail`}>
                      <td colSpan={7} className="px-3 py-2 bg-muted/20">
                        {ev.error_message && (
                          <p className="text-destructive text-xs mb-2">{ev.error_message}</p>
                        )}
                        <pre className="text-xs bg-background p-2 rounded border border-border overflow-auto">
{JSON.stringify(ev.raw_payload, null, 2)}
                        </pre>
                      </td>
                    </tr>
                  )}
                </>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div className="flex justify-between mt-3">
        <Button
          variant="outline"
          size="sm"
          disabled={pageIndex === 0}
          onClick={() => setPageIndex((p) => Math.max(0, p - 1))}
        >
          ← Trước
        </Button>
        <Button variant="outline" size="sm" onClick={() => setPageIndex((p) => p + 1)}>
          Sau →
        </Button>
      </div>
    </AdminLayout>
  )
}
