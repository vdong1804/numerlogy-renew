/**
 * Dashboard card showing remaining download quota with a progress bar.
 */
import { Download } from 'lucide-react'

interface Props {
  used: number
  total: number
  remaining: number
}

export default function DashboardQuotaCard({ used, total, remaining }: Props) {
  const safeTotal = total > 0 ? total : 1
  const pct = Math.min(100, Math.round((used / safeTotal) * 100))

  return (
    <div className="rounded-xl border border-border bg-card p-5">
      <div className="flex items-center justify-between">
        <p className="text-xs uppercase tracking-wide text-muted-foreground">
          Lượt tải còn lại
        </p>
        <Download className="w-4 h-4 text-muted-foreground" />
      </div>
      <p className="text-3xl font-bold mt-1">{remaining}</p>
      <div className="mt-3 h-2 w-full rounded-full bg-muted overflow-hidden">
        <div
          className="h-full bg-primary transition-all"
          style={{ width: `${pct}%` }}
        />
      </div>
      <p className="text-xs text-muted-foreground mt-2">
        Đã dùng {used}/{total > 0 ? total : '—'}
      </p>
    </div>
  )
}
