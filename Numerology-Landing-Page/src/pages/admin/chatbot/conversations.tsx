/**
 * Admin chatbot conversations browser.
 * Route: /admin/chatbot/conversations
 *
 * Filters: user_id, tier, date range. Click a row to open a modal with the
 * full thread + citations.
 */
import { useCallback, useEffect, useMemo, useState } from 'react'
import type { CellContext, ColumnDef } from '@tanstack/react-table'
import { Eye } from 'lucide-react'

import AdminLayout from '@/components/admin/admin-layout'
import { AdminPageHeader, ErrorBanner } from '@/components/admin/admin-page-header'
import ContentTable from '@/components/admin/content-table'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { getJson } from '@/lib/admin-api'
import { formatDateVi } from '@/lib/utils'
import ConversationViewer from '@/modules/admin/chatbot/conversation-viewer'

import type {
  ConversationListItem,
  ConversationListResponse,
} from '@/modules/admin/chatbot/chatbot-types'

const PAGE_SIZE = 20

interface Filters {
  user_id: string
  tier: string
  date_from: string
  date_to: string
}

const EMPTY_FILTERS: Filters = {
  user_id: '',
  tier: '',
  date_from: '',
  date_to: '',
}

export default function ChatbotConversationsPage() {
  const [rows, setRows] = useState<ConversationListItem[]>([])
  const [total, setTotal] = useState(0)
  const [pageIndex, setPageIndex] = useState(0)
  const [filters, setFilters] = useState<Filters>(EMPTY_FILTERS)
  const [applied, setApplied] = useState<Filters>(EMPTY_FILTERS)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [openConvId, setOpenConvId] = useState<number | null>(null)

  const fetchData = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const params = new URLSearchParams({
        limit: String(PAGE_SIZE),
        offset: String(pageIndex * PAGE_SIZE),
      })
      if (applied.user_id) params.set('user_id', applied.user_id)
      if (applied.tier) params.set('tier', applied.tier)
      if (applied.date_from) params.set('date_from', applied.date_from)
      if (applied.date_to) params.set('date_to', applied.date_to)
      const resp = await getJson<ConversationListResponse>(
        `/admin/chatbot/conversations?${params}`
      )
      setRows(resp.items)
      setTotal(resp.total)
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setLoading(false)
    }
  }, [pageIndex, applied])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  const columns = useMemo<ColumnDef<ConversationListItem>[]>(
    () => [
      { accessorKey: 'id', header: 'ID', size: 70 },
      {
        accessorKey: 'user_id',
        header: 'User',
        size: 90,
        cell: ({ getValue }: CellContext<ConversationListItem, unknown>) => (
          <span className="font-mono text-xs">#{Number(getValue())}</span>
        ),
      },
      {
        accessorKey: 'title',
        header: 'Tiêu đề',
        cell: ({ getValue }: CellContext<ConversationListItem, unknown>) => (
          <span className="text-sm">{(getValue() as string | null) ?? '—'}</span>
        ),
      },
      {
        accessorKey: 'message_count',
        header: 'Tin nhắn',
        size: 90,
        cell: ({ getValue }: CellContext<ConversationListItem, unknown>) => (
          <span className="tabular-nums text-sm">{Number(getValue() ?? 0)}</span>
        ),
      },
      {
        accessorKey: 'pdf_context_id',
        header: 'PDF',
        size: 80,
        cell: ({ getValue }: CellContext<ConversationListItem, unknown>) => {
          const v = getValue() as number | null
          return v ? <Badge variant="secondary">#{v}</Badge> : <span className="text-muted-foreground text-xs">—</span>
        },
      },
      {
        accessorKey: 'created_at',
        header: 'Tạo',
        size: 160,
        cell: ({ getValue }: CellContext<ConversationListItem, unknown>) => (
          <span className="text-xs text-muted-foreground">
            {formatDateVi(getValue() as string)}
          </span>
        ),
      },
      {
        id: 'actions',
        header: '',
        size: 110,
        cell: ({ row }: CellContext<ConversationListItem, unknown>) => (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setOpenConvId(row.original.id)}
          >
            <Eye className="w-3.5 h-3.5 mr-1" /> Xem
          </Button>
        ),
      },
    ],
    []
  )

  function applyFilters() {
    setPageIndex(0)
    setApplied(filters)
  }

  function clearFilters() {
    setFilters(EMPTY_FILTERS)
    setApplied(EMPTY_FILTERS)
    setPageIndex(0)
  }

  return (
    <AdminLayout title="Hội thoại">
      <AdminPageHeader
        title="Hội thoại chatbot"
        description="Duyệt và kiểm tra nội dung chat của người dùng. Lọc theo user, tier hoặc khoảng thời gian."
      />
      <ErrorBanner message={error} />

      <Card className="mb-4">
        <CardContent className="p-4 grid grid-cols-1 md:grid-cols-5 gap-3 items-end">
          <div>
            <label className="text-xs text-muted-foreground" htmlFor="f-user">User ID</label>
            <Input
              id="f-user"
              type="number"
              value={filters.user_id}
              onChange={(e) => setFilters({ ...filters, user_id: e.target.value })}
              placeholder="42"
            />
          </div>
          <div>
            <label className="text-xs text-muted-foreground" htmlFor="f-tier">Tier</label>
            <Input
              id="f-tier"
              value={filters.tier}
              onChange={(e) => setFilters({ ...filters, tier: e.target.value })}
              placeholder="free | paid"
            />
          </div>
          <div>
            <label className="text-xs text-muted-foreground" htmlFor="f-from">Từ ngày</label>
            <Input
              id="f-from"
              type="date"
              value={filters.date_from}
              onChange={(e) => setFilters({ ...filters, date_from: e.target.value })}
            />
          </div>
          <div>
            <label className="text-xs text-muted-foreground" htmlFor="f-to">Đến ngày</label>
            <Input
              id="f-to"
              type="date"
              value={filters.date_to}
              onChange={(e) => setFilters({ ...filters, date_to: e.target.value })}
            />
          </div>
          <div className="flex gap-2">
            <Button onClick={applyFilters} className="flex-1">Lọc</Button>
            <Button variant="ghost" onClick={clearFilters}>Xóa</Button>
          </div>
        </CardContent>
      </Card>

      <ContentTable
        columns={columns}
        rows={rows}
        pageCount={Math.max(1, Math.ceil(total / PAGE_SIZE))}
        pageIndex={pageIndex}
        pageSize={PAGE_SIZE}
        loading={loading}
        totalCount={total}
        searchValue=""
        searchPlaceholder="Dùng bộ lọc bên trên..."
        onSearch={() => undefined}
        onPaginationChange={(pi) => setPageIndex(pi)}
      />

      <ConversationViewer
        conversationId={openConvId}
        onClose={() => setOpenConvId(null)}
      />
    </AdminLayout>
  )
}
