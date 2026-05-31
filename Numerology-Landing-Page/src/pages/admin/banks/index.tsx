/**
 * Admin banks list page.
 * Route: /admin/banks
 */
import type { ColumnDef, CellContext } from '@tanstack/react-table'
import Link from 'next/link'
import { useCallback, useEffect, useMemo, useState } from 'react'
import { Landmark, Pencil, Trash2 } from 'lucide-react'

import AdminLayout from '@/components/admin/admin-layout'
import { AdminPageHeader, ErrorBanner } from '@/components/admin/admin-page-header'
import ConfirmDialog from '@/components/admin/confirm-dialog'
import ContentTable from '@/components/admin/content-table'
import { toast } from '@/components/admin/admin-toast'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { del, getJson } from '@/lib/admin-api'

const PAGE_SIZE = 50

interface BankRow {
  id: number
  bank: string
  branch?: string | null
  account_number: string
  account_holder: string
  image?: string | null
  code?: string | null
}

interface BanksResponse {
  items: BankRow[]
  total: number
}

export default function BanksListPage() {
  const [rows, setRows] = useState<BankRow[]>([])
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
      const data = await getJson<BanksResponse>(`/admin/banks?${params}`)
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
      await del(`/admin/banks/${deleteId}`)
      toast.success(`Đã xóa ngân hàng #${deleteId}`)
      setDeleteId(null)
      fetchData()
    } catch (err) {
      toast.error((err as Error).message)
      setDeleteId(null)
    } finally {
      setDeleting(false)
    }
  }

  const columns = useMemo<ColumnDef<BankRow>[]>(
    () => [
      { accessorKey: 'id', header: 'ID', size: 60 },
      {
        accessorKey: 'bank',
        header: 'Ngân hàng',
        cell: ({ row }: CellContext<BankRow, unknown>) => (
          <div className="flex items-center gap-2.5">
            <span className="flex items-center justify-center w-8 h-8 rounded-lg bg-primary/10 text-primary">
              <Landmark className="w-4 h-4" />
            </span>
            <div className="flex flex-col">
              <span className="text-sm font-medium">{row.original.bank}</span>
              {row.original.branch && (
                <span className="text-xs text-muted-foreground">{row.original.branch}</span>
              )}
            </div>
          </div>
        ),
      },
      {
        accessorKey: 'account_number',
        header: 'Số tài khoản',
        cell: ({ getValue }: CellContext<BankRow, unknown>) => (
          <span className="font-mono text-sm">{String(getValue() ?? '—')}</span>
        ),
      },
      { accessorKey: 'account_holder', header: 'Chủ tài khoản' },
      {
        accessorKey: 'code',
        header: 'Mã',
        cell: ({ getValue }: CellContext<BankRow, unknown>) => {
          const v = getValue() as string | undefined
          return v ? <Badge variant="outline" className="font-mono">{v}</Badge> : <span className="text-muted-foreground text-xs">—</span>
        },
      },
      {
        id: 'actions',
        header: '',
        size: 140,
        cell: ({ row }: CellContext<BankRow, unknown>) => (
          <div className="flex items-center gap-1 justify-end">
            <Button asChild variant="ghost" size="sm">
              <Link href={`/admin/banks/${row.original.id}`}>
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
    <AdminLayout title="Ngân hàng">
      <AdminPageHeader
        title="Ngân hàng"
        description="Tài khoản nhận thanh toán"
        primaryAction={{ href: '/admin/banks/new', label: 'Thêm ngân hàng' }}
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
        searchPlaceholder="Tìm theo tên ngân hàng, mã..."
        onPaginationChange={(pi) => setPageIndex(pi)}
        onSearch={(q) => {
          setSearch(q)
          setPageIndex(0)
        }}
        searchValue={search}
      />
      <ConfirmDialog
        open={deleteId !== null}
        title="Xóa ngân hàng"
        message={`Xác nhận xóa ngân hàng #${deleteId}? Hành động này không thể hoàn tác.`}
        confirmLabel="Xóa vĩnh viễn"
        danger
        loading={deleting}
        onConfirm={handleDelete}
        onCancel={() => setDeleteId(null)}
      />
    </AdminLayout>
  )
}
