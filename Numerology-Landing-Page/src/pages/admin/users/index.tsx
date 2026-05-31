/**
 * Admin users list page — paginated with search.
 * Route: /admin/users
 */
import type { ColumnDef, CellContext } from '@tanstack/react-table'
import Link from 'next/link'
import { useCallback, useEffect, useMemo, useState } from 'react'
import { Check, Eye, Minus, Shield, X } from 'lucide-react'

import AdminLayout from '@/components/admin/admin-layout'
import { AdminPageHeader, ErrorBanner } from '@/components/admin/admin-page-header'
import ContentTable from '@/components/admin/content-table'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { getJson } from '@/lib/admin-api'
import { formatDateVi } from '@/lib/utils'

const PAGE_SIZE = 50

interface UserRow {
  id: number
  email: string
  full_name?: string
  is_active: boolean
  is_superuser: boolean
  created_at: string
}

interface UsersResponse {
  items: UserRow[]
  total: number
}

export default function UsersListPage() {
  const [rows, setRows] = useState<UserRow[]>([])
  const [total, setTotal] = useState(0)
  const [pageIndex, setPageIndex] = useState(0)
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const fetchData = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const params = new URLSearchParams({
        limit: String(PAGE_SIZE),
        offset: String(pageIndex * PAGE_SIZE),
        ...(search ? { q: search } : {}),
      })
      const data = await getJson<UsersResponse>(`/admin/users?${params}`)
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

  const columns = useMemo<ColumnDef<UserRow>[]>(
    () => [
      { accessorKey: 'id', header: 'ID', size: 60 },
      {
        accessorKey: 'email',
        header: 'Email',
        cell: ({ row }: CellContext<UserRow, unknown>) => {
          const u = row.original
          const initial = (u.full_name || u.email).slice(0, 1).toUpperCase()
          return (
            <div className="flex items-center gap-2.5">
              <span className="flex items-center justify-center w-8 h-8 rounded-full bg-primary/10 text-primary text-xs font-semibold">
                {initial}
              </span>
              <div className="flex flex-col">
                <span className="text-sm font-medium">{u.full_name || '—'}</span>
                <span className="text-xs text-muted-foreground">{u.email}</span>
              </div>
            </div>
          )
        },
      },
      {
        accessorKey: 'is_active',
        header: 'Trạng thái',
        cell: ({ getValue }: CellContext<UserRow, unknown>) =>
          getValue() ? (
            <Badge variant="success" className="gap-1">
              <Check className="w-3 h-3" /> Kích hoạt
            </Badge>
          ) : (
            <Badge variant="destructive" className="gap-1">
              <X className="w-3 h-3" /> Khóa
            </Badge>
          ),
      },
      {
        accessorKey: 'is_superuser',
        header: 'Vai trò',
        cell: ({ getValue }: CellContext<UserRow, unknown>) =>
          getValue() ? (
            <Badge variant="accent" className="gap-1">
              <Shield className="w-3 h-3" /> Admin
            </Badge>
          ) : (
            <span className="inline-flex items-center gap-1 text-xs text-muted-foreground">
              <Minus className="w-3 h-3" /> Người dùng
            </span>
          ),
      },
      {
        accessorKey: 'created_at',
        header: 'Ngày tạo',
        cell: ({ getValue }: CellContext<UserRow, unknown>) => (
          <span className="text-xs text-muted-foreground">{formatDateVi(getValue() as string)}</span>
        ),
      },
      {
        id: 'actions',
        header: '',
        size: 80,
        cell: ({ row }: CellContext<UserRow, unknown>) => (
          <Button asChild variant="ghost" size="sm" className="text-primary">
            <Link href={`/admin/users/${row.original.id}`}>
              <Eye className="w-3.5 h-3.5" /> Xem
            </Link>
          </Button>
        ),
      },
    ],
    []
  )

  return (
    <AdminLayout title="Người dùng">
      <AdminPageHeader title="Người dùng" description="Quản lý khách hàng và quyền hạn" />
      <ErrorBanner message={error} />
      <ContentTable
        columns={columns}
        rows={rows}
        pageCount={Math.ceil(total / PAGE_SIZE)}
        pageIndex={pageIndex}
        pageSize={PAGE_SIZE}
        loading={loading}
        totalCount={total}
        searchPlaceholder="Tìm theo email, họ tên..."
        onPaginationChange={(pi) => setPageIndex(pi)}
        onSearch={(q) => {
          setSearch(q)
          setPageIndex(0)
        }}
        searchValue={search}
      />
    </AdminLayout>
  )
}
