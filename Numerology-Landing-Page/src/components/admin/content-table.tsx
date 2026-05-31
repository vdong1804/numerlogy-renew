/**
 * Reusable admin data table — search + pagination + loading overlay.
 * Uses @tanstack/react-table for column definitions and our shadcn table primitives.
 */
import * as React from 'react'
import {
  flexRender,
  getCoreRowModel,
  type ColumnDef,
  type PaginationState,
  type Updater,
  useReactTable,
} from '@tanstack/react-table'
import { ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight, Search, X } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { cn } from '@/lib/utils'

interface ContentTableProps<T> {
  columns: ColumnDef<T>[]
  rows: T[]
  pageCount: number
  pageIndex: number
  pageSize: number
  onPaginationChange: (pageIndex: number, pageSize: number) => void
  onSearch: (q: string) => void
  searchValue?: string
  searchPlaceholder?: string
  loading?: boolean
  emptyMessage?: string
  totalCount?: number
}

export default function ContentTable<T>({
  columns,
  rows,
  pageCount,
  pageIndex,
  pageSize,
  onPaginationChange,
  onSearch,
  searchValue = '',
  searchPlaceholder = 'Tìm theo code, tiêu đề...',
  loading = false,
  emptyMessage = 'Không có dữ liệu',
  totalCount,
}: ContentTableProps<T>) {
  const [localSearch, setLocalSearch] = React.useState(searchValue)

  // Debounce search input
  React.useEffect(() => {
    if (localSearch === searchValue) return
    const t = setTimeout(() => onSearch(localSearch), 350)
    return () => clearTimeout(t)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [localSearch])

  const table = useReactTable({
    data: rows,
    columns,
    pageCount,
    state: { pagination: { pageIndex, pageSize } },
    manualPagination: true,
    getCoreRowModel: getCoreRowModel(),
    onPaginationChange: (updater: Updater<PaginationState>) => {
      const next = typeof updater === 'function' ? updater({ pageIndex, pageSize }) : updater
      onPaginationChange(next.pageIndex, next.pageSize)
    },
  })

  const showingFrom = pageIndex * pageSize + 1
  const showingTo = Math.min((pageIndex + 1) * pageSize, totalCount ?? rows.length + pageIndex * pageSize)

  return (
    <div className="space-y-3">
      {/* Search toolbar */}
      <div className="flex items-center gap-2">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input
            value={localSearch}
            onChange={(e) => setLocalSearch(e.target.value)}
            placeholder={searchPlaceholder}
            className="pl-9 pr-9"
          />
          {localSearch && (
            <button
              type="button"
              onClick={() => setLocalSearch('')}
              className="absolute right-2 top-1/2 -translate-y-1/2 p-1 text-muted-foreground hover:text-foreground"
              aria-label="Xóa tìm kiếm"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
        {typeof totalCount === 'number' && (
          <span className="text-xs text-muted-foreground whitespace-nowrap">
            {totalCount.toLocaleString('vi-VN')} kết quả
          </span>
        )}
      </div>

      {/* Table card */}
      <Card className="overflow-hidden">
        <div className="relative">
          {loading && (
            <div className="absolute inset-0 z-10 flex items-center justify-center bg-background/70 backdrop-blur-sm">
              <span className="w-6 h-6 rounded-full border-2 border-primary/30 border-t-primary animate-spin" />
            </div>
          )}
          <Table>
            <TableHeader>
              {table.getHeaderGroups().map((hg) => (
                <TableRow key={hg.id} className="hover:bg-transparent">
                  {hg.headers.map((h) => (
                    <TableHead key={h.id} style={{ width: h.column.columnDef.size }}>
                      {flexRender(h.column.columnDef.header, h.getContext())}
                    </TableHead>
                  ))}
                </TableRow>
              ))}
            </TableHeader>
            <TableBody>
              {table.getRowModel().rows.length === 0 ? (
                <TableRow className="hover:bg-transparent">
                  <TableCell colSpan={columns.length} className="text-center py-10 text-muted-foreground">
                    {emptyMessage}
                  </TableCell>
                </TableRow>
              ) : (
                table.getRowModel().rows.map((row) => (
                  <TableRow key={row.id}>
                    {row.getVisibleCells().map((cell) => (
                      <TableCell key={cell.id}>
                        {flexRender(cell.column.columnDef.cell, cell.getContext())}
                      </TableCell>
                    ))}
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>
      </Card>

      {/* Pagination */}
      <div className="flex items-center justify-between gap-2 text-sm">
        <span className="text-xs text-muted-foreground">
          {rows.length > 0 ? `Hiển thị ${showingFrom}–${showingTo}` : 'Không có dòng nào'}
          {typeof totalCount === 'number' ? ` / ${totalCount.toLocaleString('vi-VN')}` : ''}
        </span>
        <div className="flex items-center gap-1">
          <PageBtn onClick={() => onPaginationChange(0, pageSize)} disabled={pageIndex === 0}>
            <ChevronsLeft className="w-4 h-4" />
          </PageBtn>
          <PageBtn onClick={() => onPaginationChange(pageIndex - 1, pageSize)} disabled={pageIndex === 0}>
            <ChevronLeft className="w-4 h-4" />
          </PageBtn>
          <span className="px-3 text-xs text-muted-foreground tabular-nums">
            Trang <span className="text-foreground font-medium">{pageIndex + 1}</span> / {pageCount || 1}
          </span>
          <PageBtn onClick={() => onPaginationChange(pageIndex + 1, pageSize)} disabled={pageIndex >= pageCount - 1}>
            <ChevronRight className="w-4 h-4" />
          </PageBtn>
          <PageBtn onClick={() => onPaginationChange(pageCount - 1, pageSize)} disabled={pageIndex >= pageCount - 1}>
            <ChevronsRight className="w-4 h-4" />
          </PageBtn>
        </div>
      </div>
    </div>
  )
}

function PageBtn({
  children,
  onClick,
  disabled,
}: {
  children: React.ReactNode
  onClick: () => void
  disabled?: boolean
}) {
  return (
    <Button
      type="button"
      variant="outline"
      size="icon"
      onClick={onClick}
      disabled={disabled}
      className={cn('h-8 w-8')}
    >
      {children}
    </Button>
  )
}
