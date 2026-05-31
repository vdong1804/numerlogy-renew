/**
 * Admin orders list — /admin/orders
 * Features: advanced search/filter form, CSV export, pagination, empty state.
 */
import DownloadIcon from '@mui/icons-material/Download'
import InboxIcon from '@mui/icons-material/Inbox'
import type { ColumnDef, CellContext } from '@tanstack/react-table'
import Link from 'next/link'
import { useCallback, useEffect, useMemo, useState } from 'react'

import AdminLayout from '@/components/admin/admin-layout'
import { AdminPageHeader, ErrorBanner } from '@/components/admin/admin-page-header'
import ContentTable from '@/components/admin/content-table'
import EmptyState from '@/components/empty-state'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  searchOrders,
  exportOrdersCsv,
  type AdminOrderSummary,
  type OrderSearchFilters,
} from '@/lib/admin-dashboard-api'
import { formatVnd } from '@/lib/utils'

import OrderSearchForm from '@/components/admin/order-search-form'

const PAGE_SIZE = 50

const STATUS_LABEL: Record<string, string> = {
  pending: 'Chờ TT',
  paid: 'Đã trả',
  cancelled: 'Hủy',
  expired: 'Hết hạn',
  failed: 'Lỗi',
  refunded: 'Hoàn tiền',
}

const EMPTY_FILTERS: OrderSearchFilters = {
  email: undefined,
  ref_code: undefined,
  status: undefined,
  date_from: undefined,
  date_to: undefined,
  page: 0,
  page_size: PAGE_SIZE,
}

export default function AdminOrdersListPage() {
  const [rows, setRows] = useState<AdminOrderSummary[]>([])
  const [total, setTotal] = useState(0)
  const [filters, setFilters] = useState<OrderSearchFilters>(EMPTY_FILTERS)
  const [pendingFilters, setPendingFilters] = useState<OrderSearchFilters>(EMPTY_FILTERS)
  const [loading, setLoading] = useState(false)
  const [exporting, setExporting] = useState(false)
  const [error, setError] = useState('')

  const fetchData = useCallback(async (activeFilters: OrderSearchFilters) => {
    setLoading(true)
    setError('')
    try {
      const res = await searchOrders(activeFilters)
      setRows(res.items)
      setTotal(res.total)
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchData(filters)
  }, [fetchData, filters])

  const handleSearch = () => {
    const next = { ...pendingFilters, page: 0 }
    setFilters(next)
  }

  const handleReset = () => {
    setPendingFilters(EMPTY_FILTERS)
    setFilters(EMPTY_FILTERS)
  }

  const handlePageChange = (pageIndex: number) => {
    const next = { ...filters, page: pageIndex }
    setFilters(next)
  }

  const handleExportCsv = async () => {
    setExporting(true)
    try {
      await exportOrdersCsv(filters)
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setExporting(false)
    }
  }

  const columns = useMemo<ColumnDef<AdminOrderSummary>[]>(
    () => [
      { accessorKey: 'id', header: 'ID', size: 60 },
      {
        accessorKey: 'ref_code',
        header: 'Mã đơn',
        cell: ({ row }: CellContext<AdminOrderSummary, unknown>) => (
          <Link className="font-mono text-primary hover:underline" href={`/admin/orders/${row.original.id}`}>
            {row.original.ref_code}
          </Link>
        ),
      },
      { accessorKey: 'user_id', header: 'User', size: 70 },
      {
        accessorKey: 'total_amount',
        header: 'Số tiền',
        cell: ({ getValue }: CellContext<AdminOrderSummary, unknown>) => (
          <span className="font-semibold">{formatVnd(getValue() as number)}</span>
        ),
      },
      {
        accessorKey: 'status',
        header: 'Trạng thái',
        size: 100,
        cell: ({ getValue }: CellContext<AdminOrderSummary, unknown>) => (
          <Badge variant={getValue() === 'paid' ? 'default' : 'outline'}>
            {STATUS_LABEL[getValue() as string] ?? String(getValue())}
          </Badge>
        ),
      },
      {
        accessorKey: 'created_at',
        header: 'Tạo lúc',
        cell: ({ getValue }: CellContext<AdminOrderSummary, unknown>) => (
          <span className="text-muted-foreground text-xs">
            {new Date(getValue() as string).toLocaleString('vi-VN')}
          </span>
        ),
      },
    ],
    []
  )

  const pageIndex = filters.page ?? 0

  return (
    <AdminLayout title="Đơn hàng">
      <AdminPageHeader title="Đơn hàng" description="Quản lý giao dịch" />

      <OrderSearchForm
        filters={pendingFilters}
        onChange={setPendingFilters}
        onSearch={handleSearch}
        onReset={handleReset}
        loading={loading}
      />

      <div className="flex justify-between items-center mb-3">
        <span className="text-sm text-muted-foreground">
          {total > 0 ? `${total} đơn hàng` : ''}
        </span>
        <Button
          size="sm"
          variant="outline"
          onClick={handleExportCsv}
          disabled={exporting || loading}
          className="gap-1.5"
        >
          <DownloadIcon fontSize="small" />
          {exporting ? 'Đang xuất...' : 'Xuất CSV'}
        </Button>
      </div>

      <ErrorBanner message={error} />

      {!loading && rows.length === 0 ? (
        <EmptyState
          icon={<InboxIcon fontSize="inherit" />}
          title="Không tìm thấy đơn hàng"
          description="Thử thay đổi bộ lọc hoặc xóa tìm kiếm để xem tất cả đơn hàng."
        />
      ) : (
        <ContentTable
          columns={columns}
          rows={rows}
          pageCount={Math.ceil(total / PAGE_SIZE)}
          pageIndex={pageIndex}
          pageSize={PAGE_SIZE}
          loading={loading}
          totalCount={total}
          onPaginationChange={handlePageChange}
          onSearch={() => { /* handled by search form */ }}
        />
      )}
    </AdminLayout>
  )
}
