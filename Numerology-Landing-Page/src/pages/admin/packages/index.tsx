/**
 * Admin packages list page.
 * Route: /admin/packages
 */
import type { CellContext, ColumnDef } from '@tanstack/react-table'
import { Download, Pencil, Trash2 } from 'lucide-react'
import Link from 'next/link'
import { useCallback, useEffect, useMemo, useState } from 'react'

import AdminLayout from '@/components/admin/admin-layout'
import {
  AdminPageHeader,
  ErrorBanner,
} from '@/components/admin/admin-page-header'
import { toast } from '@/components/admin/admin-toast'
import ConfirmDialog from '@/components/admin/confirm-dialog'
import ContentTable from '@/components/admin/content-table'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { del, getJson } from '@/lib/admin-api'
import { formatVnd } from '@/lib/utils'

const PAGE_SIZE = 50

interface PackageRow {
  id: number
  name: string
  price: number
  price_sale: number
  number_download: number
  content?: string | null
  package_kind?: string | null
}

interface PackagesResponse {
  items: PackageRow[]
  total: number
}

export default function PackagesListPage() {
  const [rows, setRows] = useState<PackageRow[]>([])
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
      const data = await getJson<PackagesResponse>(`/admin/packages?${params}`)
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
      await del(`/admin/packages/${deleteId}`)
      toast.success(`Đã xóa gói #${deleteId}`)
      setDeleteId(null)
      fetchData()
    } catch (err) {
      toast.error((err as Error).message)
      setDeleteId(null)
    } finally {
      setDeleting(false)
    }
  }

  const columns = useMemo<ColumnDef<PackageRow>[]>(
    () => [
      { accessorKey: 'id', header: 'ID', size: 60 },
      {
        accessorKey: 'name',
        header: 'Tên gói',
        cell: ({ getValue }: CellContext<PackageRow, unknown>) => (
          <span className="font-medium">{String(getValue())}</span>
        ),
      },
      {
        accessorKey: 'package_kind',
        header: 'Loại',
        size: 120,
        cell: ({ getValue }: CellContext<PackageRow, unknown>) => {
          const kind = getValue() as string | null
          return kind === 'chat_addon' ? (
            <Badge className="bg-violet-100 text-violet-700 border-violet-200">
              Chat AI
            </Badge>
          ) : (
            <Badge variant="outline">PDF</Badge>
          )
        },
      },
      {
        accessorKey: 'price',
        header: 'Giá',
        cell: ({ row }: CellContext<PackageRow, unknown>) => {
          const p = row.original
          const hasSale = p.price_sale > 0 && p.price_sale < p.price
          return (
            <div className="flex flex-col">
              <span className="text-sm font-semibold">
                {formatVnd(hasSale ? p.price_sale : p.price)}
              </span>
              {hasSale && (
                <span className="text-xs text-muted-foreground line-through">
                  {formatVnd(p.price)}
                </span>
              )}
            </div>
          )
        },
      },
      {
        accessorKey: 'number_download',
        header: 'Lượt tải',
        cell: ({ getValue }: CellContext<PackageRow, unknown>) => (
          <Badge variant="outline" className="gap-1 font-mono">
            <Download className="w-3 h-3" /> {getValue() as number}
          </Badge>
        ),
      },
      {
        id: 'actions',
        header: '',
        size: 140,
        cell: ({ row }: CellContext<PackageRow, unknown>) => (
          <div className="flex items-center gap-1 justify-end">
            <Button asChild variant="ghost" size="sm">
              <Link href={`/admin/packages/${row.original.id}`}>
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
    <AdminLayout title="Gói dịch vụ">
      <AdminPageHeader
        title="Gói dịch vụ"
        description="Cấu hình gói thanh toán và quota tải PDF"
        primaryAction={{ href: '/admin/packages/new', label: 'Tạo gói mới' }}
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
        searchPlaceholder="Tìm theo tên gói..."
        onPaginationChange={(pi) => setPageIndex(pi)}
        onSearch={(q) => {
          setSearch(q)
          setPageIndex(0)
        }}
        searchValue={search}
      />
      <ConfirmDialog
        open={deleteId !== null}
        title="Xóa gói dịch vụ"
        message={`Xác nhận xóa gói #${deleteId}? Hành động này không thể hoàn tác.`}
        confirmLabel="Xóa vĩnh viễn"
        danger
        loading={deleting}
        onConfirm={handleDelete}
        onCancel={() => setDeleteId(null)}
      />
    </AdminLayout>
  )
}
