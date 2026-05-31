/**
 * Download history — /my-account/downloads
 * Lists user_downloads (PDF từ quota gói + lookup miễn phí).
 */
import HistoryOutlinedIcon from '@mui/icons-material/HistoryOutlined'
import { useEffect, useState } from 'react'

import AccountLayout from '@/components/my-account/account-layout'
import EmptyState from '@/components/empty-state'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { listMyDownloads, type MyDownloadEntry } from '@/lib/my-account-api'

const PAGE_SIZE = 20

export default function MyDownloadsPage() {
  const [items, setItems] = useState<MyDownloadEntry[]>([])
  const [total, setTotal] = useState(0)
  const [offset, setOffset] = useState(0)
  const [typeFilter, setTypeFilter] = useState<number | undefined>(undefined)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    listMyDownloads({ limit: PAGE_SIZE, offset, type: typeFilter })
      .then((res) => {
        setItems(res.items)
        setTotal(res.total)
      })
      .catch(() => undefined)
      .finally(() => setLoading(false))
  }, [offset, typeFilter])

  const hasPrev = offset > 0
  const hasNext = offset + PAGE_SIZE < total

  return (
    <AccountLayout
      title="Lịch sử tải"
      description="Các bản tra cứu / báo cáo bạn đã tạo"
    >
      <div className="flex items-center gap-2 mb-4 flex-wrap">
        <FilterChip
          label="Tất cả"
          active={typeFilter === undefined}
          onClick={() => {
            setTypeFilter(undefined)
            setOffset(0)
          }}
        />
        <FilterChip
          label="Miễn phí"
          active={typeFilter === 0}
          onClick={() => {
            setTypeFilter(0)
            setOffset(0)
          }}
        />
        <FilterChip
          label="Trả phí"
          active={typeFilter === 1}
          onClick={() => {
            setTypeFilter(1)
            setOffset(0)
          }}
        />
      </div>

      {loading ? (
        <div className="space-y-2">
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-12 w-full rounded-lg" />
          ))}
        </div>
      ) : items.length === 0 ? (
        <EmptyState
          icon={<HistoryOutlinedIcon fontSize="inherit" />}
          title="Chưa có lịch sử tải"
          description="Khi bạn tra cứu hoặc tải báo cáo, lịch sử sẽ xuất hiện tại đây."
          ctaLabel="Tra cứu ngay"
          ctaHref="/"
        />
      ) : (
        <>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="text-left text-xs uppercase text-muted-foreground">
                <tr>
                  <th className="py-2 pr-4">Họ tên</th>
                  <th className="py-2 pr-4">Ngày sinh</th>
                  <th className="py-2 pr-4">Loại</th>
                  <th className="py-2 pr-4">Thời gian</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {items.map((d) => (
                  <tr key={d.id} className="hover:bg-muted/40">
                    <td className="py-2 pr-4 font-medium">{d.name}</td>
                    <td className="py-2 pr-4 text-muted-foreground">
                      {d.birth_day ?? '—'}
                    </td>
                    <td className="py-2 pr-4">
                      <Badge variant={d.type === 1 ? 'default' : 'outline'}>
                        {d.type === 1 ? 'Trả phí' : 'Miễn phí'}
                      </Badge>
                    </td>
                    <td className="py-2 pr-4 text-muted-foreground">
                      {new Date(d.created_at).toLocaleString('vi-VN')}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="flex items-center justify-between mt-4 text-sm">
            <p className="text-muted-foreground">
              {offset + 1}–{Math.min(offset + PAGE_SIZE, total)} / {total}
            </p>
            <div className="flex gap-2">
              <Button
                size="sm"
                variant="outline"
                disabled={!hasPrev}
                onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}
              >
                ← Trước
              </Button>
              <Button
                size="sm"
                variant="outline"
                disabled={!hasNext}
                onClick={() => setOffset(offset + PAGE_SIZE)}
              >
                Sau →
              </Button>
            </div>
          </div>
        </>
      )}
    </AccountLayout>
  )
}

function FilterChip({
  label,
  active,
  onClick,
}: {
  label: string
  active: boolean
  onClick: () => void
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={
        'rounded-full px-3 py-1 text-xs transition-colors ' +
        (active
          ? 'bg-primary text-primary-foreground'
          : 'bg-muted text-muted-foreground hover:bg-muted/70')
      }
    >
      {label}
    </button>
  )
}
