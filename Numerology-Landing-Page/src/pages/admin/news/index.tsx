/**
 * Admin news list page.
 * Route: /admin/news
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
import { formatDateVi } from '@/lib/utils'

const PAGE_SIZE = 50

interface NewsRow {
  id: number
  title: string
  category?: string
  created_at: string
}

interface NewsResponse {
  items: NewsRow[]
  total: number
}

export default function NewsListPage() {
  const [rows, setRows] = useState<NewsRow[]>([])
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
      const data = await getJson<NewsResponse>(`/admin/news?${params}`)
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
      await del(`/admin/news/${deleteId}`)
      toast.success(`Đã xóa tin tức #${deleteId}`)
      setDeleteId(null)
      fetchData()
    } catch (err) {
      toast.error((err as Error).message)
      setDeleteId(null)
    } finally {
      setDeleting(false)
    }
  }

  const columns = useMemo<ColumnDef<NewsRow>[]>(
    () => [
      { accessorKey: 'id', header: 'ID', size: 60 },
      {
        accessorKey: 'title',
        header: 'Tiêu đề',
        cell: ({ getValue }: CellContext<NewsRow, unknown>) => (
          <span className="text-sm font-medium">{String(getValue() ?? '—')}</span>
        ),
      },
      {
        accessorKey: 'category',
        header: 'Danh mục',
        cell: ({ getValue }: CellContext<NewsRow, unknown>) => {
          const v = getValue() as string | undefined
          return v ? <Badge variant="secondary">{v}</Badge> : <span className="text-muted-foreground text-xs">—</span>
        },
      },
      {
        accessorKey: 'created_at',
        header: 'Ngày tạo',
        cell: ({ getValue }: CellContext<NewsRow, unknown>) => (
          <span className="text-xs text-muted-foreground">{formatDateVi(getValue() as string)}</span>
        ),
      },
      {
        id: 'actions',
        header: '',
        size: 140,
        cell: ({ row }: CellContext<NewsRow, unknown>) => (
          <div className="flex items-center gap-1 justify-end">
            <Button asChild variant="ghost" size="sm">
              <Link href={`/admin/news/${row.original.id}`}>
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
    <AdminLayout title="Tin tức">
      <AdminPageHeader
        title="Tin tức"
        description="Quản lý bài viết và danh mục tin tức"
        primaryAction={{ href: '/admin/news/new', label: 'Tạo tin mới' }}
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
        searchPlaceholder="Tìm theo tiêu đề..."
        onPaginationChange={(pi) => setPageIndex(pi)}
        onSearch={(q) => {
          setSearch(q)
          setPageIndex(0)
        }}
        searchValue={search}
      />
      <ConfirmDialog
        open={deleteId !== null}
        title="Xóa tin tức"
        message={`Xác nhận xóa tin tức #${deleteId}? Hành động này không thể hoàn tác.`}
        confirmLabel="Xóa vĩnh viễn"
        danger
        loading={deleting}
        onConfirm={handleDelete}
        onCancel={() => setDeleteId(null)}
      />
    </AdminLayout>
  )
}
