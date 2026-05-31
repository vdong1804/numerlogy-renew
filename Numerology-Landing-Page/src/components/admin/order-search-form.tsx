/**
 * Order search/filter form — used by admin orders list page.
 * Owns: email, ref_code, status, date_from, date_to inputs + search/reset buttons.
 */
import { Button } from '@/components/ui/button'
import type { OrderSearchFilters } from '@/lib/admin-dashboard-api'

const STATUS_OPTIONS: Array<{ value: string; label: string }> = [
  { value: '', label: 'Tất cả' },
  { value: 'pending', label: 'Chờ thanh toán' },
  { value: 'paid', label: 'Đã thanh toán' },
  { value: 'refunded', label: 'Đã hoàn tiền' },
  { value: 'expired', label: 'Hết hạn' },
  { value: 'cancelled', label: 'Đã hủy' },
]

interface Props {
  filters: OrderSearchFilters
  onChange: (updated: OrderSearchFilters) => void
  onSearch: () => void
  onReset: () => void
  loading?: boolean
}

/**
 * Convert a YYYY-MM-DD date string to an ISO 8601 datetime with Bangkok (+07:00) offset.
 * Contract with backend: frontend always sends tz-aware datetimes so the backend
 * can compare directly against UTC-stored timestamps without guessing the timezone.
 * date_from → start of day 00:00:00+07:00
 * date_to   → end of day 23:59:59+07:00 (inclusive)
 */
function toIsoWithBangkokTz(dateStr: string, endOfDay = false): string {
  const time = endOfDay ? '23:59:59' : '00:00:00'
  return `${dateStr}T${time}+07:00`
}

export default function OrderSearchForm({ filters, onChange, onSearch, onReset, loading }: Props) {
  const set = (key: keyof OrderSearchFilters, value: string) =>
    onChange({ ...filters, [key]: value || undefined })

  /** Extract YYYY-MM-DD portion from a stored ISO datetime string (for date input display). */
  const toDateInputValue = (iso?: string) => iso ? iso.slice(0, 10) : ''

  const setDate = (key: 'date_from' | 'date_to', rawDate: string) => {
    if (!rawDate) {
      onChange({ ...filters, [key]: undefined })
      return
    }
    const iso = toIsoWithBangkokTz(rawDate, key === 'date_to')
    onChange({ ...filters, [key]: iso })
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') onSearch()
  }

  return (
    <div className="flex flex-wrap gap-2 mb-4 items-end">
      {/* Email */}
      <div className="flex flex-col gap-1">
        <label className="text-xs text-muted-foreground">Email</label>
        <input
          type="text"
          placeholder="user@example.com"
          value={filters.email ?? ''}
          onChange={(e) => set('email', e.target.value)}
          onKeyDown={handleKeyDown}
          className="h-8 px-2 text-sm border rounded-md focus:outline-none focus:ring-1 focus:ring-primary w-44"
        />
      </div>

      {/* Ref code */}
      <div className="flex flex-col gap-1">
        <label className="text-xs text-muted-foreground">Mã đơn</label>
        <input
          type="text"
          placeholder="REF-..."
          value={filters.ref_code ?? ''}
          onChange={(e) => set('ref_code', e.target.value)}
          onKeyDown={handleKeyDown}
          className="h-8 px-2 text-sm border rounded-md focus:outline-none focus:ring-1 focus:ring-primary w-32"
        />
      </div>

      {/* Status */}
      <div className="flex flex-col gap-1">
        <label className="text-xs text-muted-foreground">Trạng thái</label>
        <select
          value={filters.status ?? ''}
          onChange={(e) => set('status', e.target.value)}
          className="h-8 px-2 text-sm border rounded-md focus:outline-none focus:ring-1 focus:ring-primary w-36 bg-background"
        >
          {STATUS_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>
              {o.label}
            </option>
          ))}
        </select>
      </div>

      {/* Date from — stored as ISO 8601 with +07:00 (Bangkok TZ) */}
      <div className="flex flex-col gap-1">
        <label className="text-xs text-muted-foreground">Từ ngày</label>
        <input
          type="date"
          value={toDateInputValue(filters.date_from)}
          onChange={(e) => setDate('date_from', e.target.value)}
          className="h-8 px-2 text-sm border rounded-md focus:outline-none focus:ring-1 focus:ring-primary w-36"
        />
      </div>

      {/* Date to — stored as ISO 8601 with +07:00 end-of-day (inclusive) */}
      <div className="flex flex-col gap-1">
        <label className="text-xs text-muted-foreground">Đến ngày</label>
        <input
          type="date"
          value={toDateInputValue(filters.date_to)}
          onChange={(e) => setDate('date_to', e.target.value)}
          className="h-8 px-2 text-sm border rounded-md focus:outline-none focus:ring-1 focus:ring-primary w-36"
        />
      </div>

      {/* Actions */}
      <div className="flex gap-2 self-end">
        <Button size="sm" onClick={onSearch} disabled={loading}>
          Tìm kiếm
        </Button>
        <Button size="sm" variant="outline" onClick={onReset} disabled={loading}>
          Xóa lọc
        </Button>
      </div>
    </div>
  )
}
