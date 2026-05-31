/**
 * Admin products list page.
 * Route: /admin/products
 */
import type { ColumnDef, CellContext } from '@tanstack/react-table'
import Link from 'next/link'
import { useCallback, useEffect, useMemo, useState } from 'react'
import { Pencil, Trash2 } from 'lucide-react'

import AdminLayout from '@/components/admin/admin-layout'
import { AdminPageHeader, ErrorBanner } from '@/components/admin/admin-page-header'
import ConfirmDialog from '@/components/admin/confirm-dialog'
import ContentTable from '@/components/admin/content-table'
import { toast } from '@/components/admin/admin-toast'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { del, getJson } from '@/lib/admin-api'
import { formatVnd } from '@/lib/utils'

const PAGE_SIZE = 50

interface ProductRow {
  id: number
  sku: string
  type: 'package' | 'report' | 'combo'
  name: string
  slug: string
  price: number
  is_active: boolean
  sort_order: number
}

interface ProductsResponse {
  items: ProductRow[]
  total: number
}

const TYPE_BADGE: Record<ProductRow['type'], string> = {
  package: 'Gói',
  report: 'Báo cáo',
  combo: 'Combo',
}

export default function ProductsListPage() {
  const [rows, setRows] = useState<ProductRow[]>([])
  const [total, setTotal] = useState(0)
  const [pageIndex, setPageIndex] = useState(0)
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [deleteId, setDeleteId] = useState<number | null>(null)
  const [deleting, setDeleting] = useState(false)

  const fetchData = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const params = new URLSearchParams({
        limit: String(PAGE_SIZE),
        offset: String(pageIndex * PAGE_SIZE),
        ...(search ? { q: search } : {}),
      })
      const data = await getJson<ProductsResponse>(`/admin/products?${params}`)
      setRows(data.items ?? [])
      setTotal(data.total ?? 0)
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setLoading(false)
    }
  }, [pageIndex, search])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  const handleDelete = async () => {
    if (!deleteId) return
    setDeleting(true)
    try {
      await del(`/admin/products/${deleteId}`)
      toast.success(`Đã xóa sản phẩm #${deleteId}`)
      setDeleteId(null)
      fetchData()
    } catch (err) {
      toast.error((err as Error).message)
      setDeleteId(null)
    } finally {
      setDeleting(false)
    }
  }

  const columns = useMemo<ColumnDef<ProductRow>[]>(
    () => [
      { accessorKey: 'id', header: 'ID', size: 60 },
      {
        accessorKey: 'sku',
        header: 'SKU',
        cell: ({ getValue }: CellContext<ProductRow, unknown>) => (
          <code className="text-xs">{String(getValue())}</code>
        ),
      },
      {
        accessorKey: 'type',
        header: 'Loại',
        size: 90,
        cell: ({ getValue }: CellContext<ProductRow, unknown>) => (
          <Badge variant="outline">{TYPE_BADGE[getValue() as ProductRow['type']]}</Badge>
        ),
      },
      {
        accessorKey: 'name',
        header: 'Tên sản phẩm',
        cell: ({ getValue }: CellContext<ProductRow, unknown>) => (
          <span className="font-medium">{String(getValue())}</span>
        ),
      },
      {
        accessorKey: 'price',
        header: 'Giá',
        cell: ({ getValue }: CellContext<ProductRow, unknown>) => (
          <span className="font-semibold">{formatVnd(getValue() as number)}</span>
        ),
      },
      {
        accessorKey: 'is_active',
        header: 'Trạng thái',
        size: 100,
        cell: ({ getValue }: CellContext<ProductRow, unknown>) =>
          (getValue() as boolean) ? (
            <Badge>Đang bán</Badge>
          ) : (
            <Badge variant="outline">Tắt</Badge>
          ),
      },
      {
        id: 'actions',
        header: '',
        size: 140,
        cell: ({ row }: CellContext<ProductRow, unknown>) => (
          <div className="flex items-center gap-1 justify-end">
            <Button asChild variant="ghost" size="sm">
              <Link href={`/admin/products/${row.original.id}`}>
                <Pencil className="w-3.5 h-3.5" /> Sửa
              </Link>
            </Button>
            <Button
              variant="ghost"
              size="sm"
              className="text-destructive hover:text-destructive hover:bg-destructive/10"
              onClick={() => setDeleteId(row.original.id)}
            >
              <Trash2 className="w-3.5 h-3.5" /> Xóa
            </Button>
          </div>
        ),
      },
    ],
    []
  )

  return (
    <AdminLayout title="Sản phẩm">
      <AdminPageHeader
        title="Sản phẩm"
        description="Catalogue gói, báo cáo lẻ và combo"
        primaryAction={{ href: '/admin/products/new', label: 'Tạo sản phẩm' }}
      />
      <ErrorBanner message={error} />
      <ContentTable
        columns={columns}
        rows={rows}
        pageCount={Math.ceil(total / PAGE_SIZE)}
        pageIndex={pageIndex}
        pageSize={PAGE_SIZE}
        loading={loading}
        totalCount={total}
        searchPlaceholder="Tìm theo SKU / tên..."
        onPaginationChange={(pi) => setPageIndex(pi)}
        onSearch={(q) => {
          setSearch(q)
          setPageIndex(0)
        }}
        searchValue={search}
      />
      <ConfirmDialog
        open={deleteId !== null}
        title="Xóa sản phẩm"
        message={`Xác nhận xóa sản phẩm #${deleteId}? Hành động này không thể hoàn tác.`}
        confirmLabel="Xóa vĩnh viễn"
        danger
        loading={deleting}
        onConfirm={handleDelete}
        onCancel={() => setDeleteId(null)}
      />
    </AdminLayout>
  )
}
