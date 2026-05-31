/**
 * Sortable table of admin-managed KB documents with delete action.
 * Reuses ContentTable (TanStack React Table) for consistent admin UX.
 */
import { useMemo, useState } from 'react'
import type { CellContext, ColumnDef } from '@tanstack/react-table'
import { Trash2 } from 'lucide-react'

import ContentTable from '@/components/admin/content-table'
import ConfirmDialog from '@/components/admin/confirm-dialog'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { toast } from '@/components/admin/admin-toast'
import { del } from '@/lib/admin-api'
import { formatDateVi } from '@/lib/utils'

import type { KbDocument } from './chatbot-types'

interface Props {
  rows: KbDocument[]
  total: number
  loading: boolean
  pageIndex: number
  pageSize: number
  onPaginationChange: (pi: number) => void
  onDeleted: () => void
  /** Optional — wires a search bar above the table. Omit to disable search. */
  search?: string
  onSearch?: (q: string) => void
}

export default function KbDocumentList({
  rows,
  total,
  loading,
  pageIndex,
  pageSize,
  onPaginationChange,
  onDeleted,
  search = '',
  onSearch,
}: Props) {
  const [deleteId, setDeleteId] = useState<number | null>(null)
  const [deleting, setDeleting] = useState(false)

  async function handleDelete() {
    if (!deleteId) return
    setDeleting(true)
    try {
      await del(`/admin/chatbot/kb/documents/${deleteId}`)
      toast.success(`Đã xóa document #${deleteId}`)
      onDeleted()
    } catch (err) {
      toast.error((err as Error).message)
    } finally {
      setDeleteId(null)
      setDeleting(false)
    }
  }

  const columns = useMemo<ColumnDef<KbDocument>[]>(
    () => [
      { accessorKey: 'id', header: 'ID', size: 70 },
      {
        accessorKey: 'source_type',
        header: 'Nguồn',
        size: 140,
        cell: ({ getValue }: CellContext<KbDocument, unknown>) => (
          <Badge variant="secondary">{String(getValue() ?? '—')}</Badge>
        ),
      },
      {
        accessorKey: 'title',
        header: 'Tiêu đề',
        cell: ({ row }: CellContext<KbDocument, unknown>) => (
          <div className="flex flex-col">
            <span className="text-sm font-medium">
              {row.original.title ?? '—'}
            </span>
            <span className="text-xs text-muted-foreground">
              {row.original.source_ref}
            </span>
          </div>
        ),
      },
      {
        accessorKey: 'chunk_count',
        header: 'Chunks',
        size: 100,
        cell: ({ getValue }: CellContext<KbDocument, unknown>) => (
          <span className="text-sm tabular-nums">{Number(getValue() ?? 0)}</span>
        ),
      },
      {
        accessorKey: 'updated_at',
        header: 'Cập nhật',
        size: 160,
        cell: ({ getValue }: CellContext<KbDocument, unknown>) => (
          <span className="text-xs text-muted-foreground">
            {formatDateVi(getValue() as string)}
          </span>
        ),
      },
      {
        id: 'actions',
        header: '',
        size: 120,
        cell: ({ row }: CellContext<KbDocument, unknown>) => (
          <div className="flex justify-end">
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
    <>
      <ContentTable
        columns={columns}
        rows={rows}
        pageCount={Math.max(1, Math.ceil(total / pageSize))}
        pageIndex={pageIndex}
        pageSize={pageSize}
        loading={loading}
        totalCount={total}
        searchValue={search}
        searchPlaceholder="Tìm theo tiêu đề hoặc nguồn..."
        onSearch={onSearch ?? (() => undefined)}
        onPaginationChange={(pi) => onPaginationChange(pi)}
      />
      <ConfirmDialog
        open={deleteId !== null}
        title="Xóa document"
        message={`Xác nhận xóa document #${deleteId}? Các chunk liên kết sẽ bị xóa theo.`}
        confirmLabel="Xóa vĩnh viễn"
        danger
        loading={deleting}
        onConfirm={handleDelete}
        onCancel={() => setDeleteId(null)}
      />
    </>
  )
}
