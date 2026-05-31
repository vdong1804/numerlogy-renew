/**
 * Detailed analytics view — extends the dashboard with timeseries charts.
 * Route: /admin/chatbot/analytics
 */
import { useCallback, useEffect, useState } from 'react'
import { RefreshCw } from 'lucide-react'

import AdminLayout from '@/components/admin/admin-layout'
import { AdminPageHeader, ErrorBanner } from '@/components/admin/admin-page-header'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { getJson } from '@/lib/admin-api'
import {
  CostByModelChart,
  DailyMessagesChart,
} from '@/modules/admin/chatbot/analytics-charts'

import type { AnalyticsOverview } from '@/modules/admin/chatbot/chatbot-types'

const WINDOWS = [7, 14, 30, 60, 90] as const

export default function ChatbotAnalyticsPage() {
  const [days, setDays] = useState<number>(30)
  const [data, setData] = useState<AnalyticsOverview | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const resp = await getJson<AnalyticsOverview>(
        `/admin/chatbot/analytics/overview?days=${days}`
      )
      setData(resp)
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setLoading(false)
    }
  }, [days])

  useEffect(() => {
    load()
  }, [load])

  return (
    <AdminLayout title="Analytics Chatbot">
      <AdminPageHeader
        title="Analytics chi tiết"
        description={`Cửa sổ ${days} ngày · ${data?.window_start ?? '—'} → ${data?.window_end ?? '—'}`}
      >
        <div className="flex items-center gap-1 rounded-md border border-border bg-card p-0.5">
          {WINDOWS.map((d) => (
            <button
              key={d}
              type="button"
              onClick={() => setDays(d)}
              className={
                d === days
                  ? 'px-2.5 py-1 text-xs font-medium rounded bg-primary text-primary-foreground'
                  : 'px-2.5 py-1 text-xs text-muted-foreground hover:bg-accent/40 rounded'
              }
            >
              {d}d
            </button>
          ))}
        </div>
        <Button variant="outline" size="sm" onClick={load} disabled={loading}>
          <RefreshCw className={loading ? 'w-4 h-4 mr-1 animate-spin' : 'w-4 h-4 mr-1'} />
          Làm mới
        </Button>
      </AdminPageHeader>
      <ErrorBanner message={error} />

      <section className="grid gap-4 grid-cols-2 sm:grid-cols-4 mb-6">
        <KpiCard label="Tin nhắn" value={data?.total_messages} loading={loading} />
        <KpiCard label="Hội thoại" value={data?.total_conversations} loading={loading} />
        <KpiCard label="User duy nhất" value={data?.unique_users} loading={loading} />
        <KpiCard
          label="Addon đã mua"
          value={data?.addon_purchases}
          loading={loading}
        />
      </section>

      <section className="grid gap-4 grid-cols-1 lg:grid-cols-2 mb-6">
        <DailyMessagesChart data={data} loading={loading} />
        <CostByModelChart data={data} loading={loading} />
      </section>

      <section className="grid gap-4 grid-cols-1 lg:grid-cols-2 mb-6">
        <CacheStatsCard data={data} loading={loading} />
        <TopQuestionsCard data={data} loading={loading} />
      </section>
    </AdminLayout>
  )
}

function KpiCard({
  label,
  value,
  loading,
}: {
  label: string
  value: number | undefined
  loading: boolean
}) {
  return (
    <Card>
      <CardContent className="p-4">
        <p className="text-xs uppercase tracking-wide text-muted-foreground font-medium">
          {label}
        </p>
        {loading ? (
          <Skeleton className="h-7 w-16 mt-1" />
        ) : (
          <p className="mt-1 text-2xl font-bold tabular-nums">
            {(value ?? 0).toLocaleString()}
          </p>
        )}
      </CardContent>
    </Card>
  )
}

function CacheStatsCard({
  data,
  loading,
}: {
  data: AnalyticsOverview | null
  loading: boolean
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Cache</CardTitle>
        <CardDescription>Semantic + Gemini prompt cache</CardDescription>
      </CardHeader>
      <CardContent>
        {loading ? (
          <Skeleton className="h-24 w-full" />
        ) : (
          <dl className="grid grid-cols-2 gap-3 text-sm">
            <Stat label="Hit rate" value={data ? `${(data.semantic_cache_hit_rate * 100).toFixed(1)}%` : '—'} />
            <Stat label="Semantic hits" value={data?.semantic_cache_hits.toLocaleString() ?? '—'} />
            <Stat label="Semantic entries" value={data?.semantic_cache_entries.toLocaleString() ?? '—'} />
            <Stat label="Prompt handles" value={data?.prompt_cache_active_handles.toLocaleString() ?? '—'} />
            <Stat label="Tổng USD" value={data ? `$${data.estimated_total_cost_usd.toFixed(2)}` : '—'} />
          </dl>
        )}
      </CardContent>
    </Card>
  )
}

function Stat({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div>
      <dt className="text-xs text-muted-foreground">{label}</dt>
      <dd className="text-base font-semibold tabular-nums">{value}</dd>
    </div>
  )
}

function TopQuestionsCard({
  data,
  loading,
}: {
  data: AnalyticsOverview | null
  loading: boolean
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Câu hỏi phổ biến</CardTitle>
        <CardDescription>Group theo nội dung</CardDescription>
      </CardHeader>
      <CardContent>
        {loading ? (
          <Skeleton className="h-32 w-full" />
        ) : !data?.top_questions.length ? (
          <p className="text-sm text-muted-foreground">Chưa có dữ liệu.</p>
        ) : (
          <ol className="space-y-2">
            {data.top_questions.map((q, idx) => (
              <li key={idx} className="flex items-start gap-2 text-sm">
                <span className="text-xs font-mono text-muted-foreground mt-0.5 w-6 shrink-0">
                  #{idx + 1}
                </span>
                <span className="flex-1 line-clamp-2">{q.question}</span>
                <span className="text-xs tabular-nums text-muted-foreground shrink-0">
                  ×{q.count}
                </span>
              </li>
            ))}
          </ol>
        )}
      </CardContent>
    </Card>
  )
}
