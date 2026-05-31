/**
 * Admin content list page — paginated table with search.
 * Route: /admin/content/[resource]
 */
import type { ColumnDef, CellContext } from '@tanstack/react-table'
import Link from 'next/link'
import { useRouter } from 'next/router'
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
import { findResource } from '@/lib/content-resources'

const PAGE_SIZE = 50

interface ContentRow {
  id: number
  code: string
  title?: string
  number_page?: number
}

interface ContentListResponse {
  items: ContentRow[]
  total: number
}

export default function ContentListPage() {
  const router = useRouter()
  const resource = router.query.resource as string

  const [rows, setRows] = useState<ContentRow[]>([])
  const [total, setTotal] = useState(0)
  const [pageIndex, setPageIndex] = useState(0)
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(false)
  const [deleteId, setDeleteId] = useState<number | null>(null)
  const [error, setError] = useState('')
  const [deleting, setDeleting] = useState(false)

  const resourceMeta = resource ? findResource(resource) : undefined

  const fetchData = useCallback(async () => {
    if (!resource) return
    setLoading(true)
    setError('')
    try {
      const offset = pageIndex * PAGE_SIZE
      const params = new URLSearchParams({
        limit: String(PAGE_SIZE),
        offset: String(offset),
        ...(search ? { q: search } : {}),
      })
      const data = await getJson<ContentListResponse>(`/admin/content/${resource}?${params}`)
      setRows(data.items ?? [])
      setTotal(data.total ?? 0)
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setLoading(false)
    }
  }, [resource, pageIndex, search])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  const handleDelete = async () => {
    if (!deleteId) return
    setDeleting(true)
    try {
      await del(`/admin/content/${resource}/${deleteId}`)
      toast.success(`Đã xóa bản ghi #${deleteId}`)
      setDeleteId(null)
      fetchData()
    } catch (err) {
      toast.error((err as Error).message)
      setDeleteId(null)
    } finally {
      setDeleting(false)
    }
  }

  const columns = useMemo<ColumnDef<ContentRow>[]>(
    () => [
      { accessorKey: 'id', header: 'ID', size: 60 },
      {
        accessorKey: 'code',
        header: 'Code',
        size: 100,
        cell: ({ getValue }: CellContext<ContentRow, unknown>) => (
          <Badge variant="outline" className="font-mono">{String(getValue() ?? '')}</Badge>
        ),
      },
      {
        accessorKey: 'title',
        header: 'Tiêu đề',
        cell: ({ getValue }: CellContext<ContentRow, unknown>) => (
          <span className="text-sm">{String(getValue() ?? '—')}</span>
        ),
      },
      {
        accessorKey: 'number_page',
        header: 'Số trang',
        size: 100,
        cell: ({ getValue }: CellContext<ContentRow, unknown>) => {
          const v = getValue() as number | undefined
          return v != null ? (
            <span className="text-xs font-mono text-muted-foreground">{v}</span>
          ) : (
            <span className="text-muted-foreground text-xs">—</span>
          )
        },
      },
      {
        id: 'actions',
        header: '',
        size: 140,
        cell: ({ row }: CellContext<ContentRow, unknown>) => (
          <div className="flex items-center gap-1 justify-end">
            <Button asChild variant="ghost" size="sm">
              <Link href={`/admin/content/${resource}/${row.original.id}`}>
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
    [resource]
  )

  const pageCount = Math.ceil(total / PAGE_SIZE)
  const label = resourceMeta?.label ?? resource

  return (
    <AdminLayout title={label}>
      <AdminPageHeader
        title={label}
        description={resourceMeta ? `Bảng nội dung · ${resource}` : undefined}
        primaryAction={{ href: `/admin/content/${resource}/new`, label: 'Tạo bản ghi' }}
      />
      <ErrorBanner message={error} />
      <ContentTable
        columns={columns}
        rows={rows}
        pageCount={pageCount}
        pageIndex={pageIndex}
        pageSize={PAGE_SIZE}
        loading={loading}
        totalCount={total}
        searchPlaceholder="Tìm theo code, tiêu đề..."
        onPaginationChange={(pi) => setPageIndex(pi)}
        onSearch={(q) => {
          setSearch(q)
          setPageIndex(0)
        }}
        searchValue={search}
      />
      <ConfirmDialog
        open={deleteId !== null}
        title="Xóa bản ghi"
        message={`Xác nhận xóa bản ghi #${deleteId}? Hành động này không thể hoàn tác.`}
        confirmLabel="Xóa vĩnh viễn"
        danger
        loading={deleting}
        onConfirm={handleDelete}
        onCancel={() => setDeleteId(null)}
      />
    </AdminLayout>
  )
}
