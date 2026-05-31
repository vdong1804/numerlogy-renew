/**
 * Admin chatbot dashboard — usage + cost + cache stats for the RAG chatbot.
 * Route: /admin/chatbot
 */
import { useEffect, useMemo, useState } from 'react'
import {
  MessageSquare,
  Users as UsersIcon,
  DollarSign,
  Zap,
  RefreshCw,
} from 'lucide-react'

import AdminLayout from '@/components/admin/admin-layout'
import { AdminPageHeader, ErrorBanner } from '@/components/admin/admin-page-header'
import { DashboardStatCard } from '@/components/admin/dashboard-stat-card'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { getJson } from '@/lib/admin-api'

import type { AnalyticsOverview } from '@/modules/admin/chatbot/chatbot-types'

const WINDOW_DAYS = 30

export default function ChatbotDashboardPage() {
  const [data, setData] = useState<AnalyticsOverview | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const load = useMemo(
    () => async () => {
      setLoading(true)
      setError('')
      try {
        const resp = await getJson<AnalyticsOverview>(
          `/admin/chatbot/analytics/overview?days=${WINDOW_DAYS}`
        )
        setData(resp)
      } catch (err) {
        setError((err as Error).message)
      } finally {
        setLoading(false)
      }
    },
    []
  )

  useEffect(() => {
    load()
  }, [load])

  return (
    <AdminLayout title="Tổng quan Chatbot">
      <AdminPageHeader
        title="Tổng quan Chatbot RAG"
        description={`Cửa sổ ${WINDOW_DAYS} ngày gần nhất`}
      >
        <Button variant="outline" size="sm" onClick={load} disabled={loading}>
          <RefreshCw className={loading ? 'w-4 h-4 mr-1 animate-spin' : 'w-4 h-4 mr-1'} />
          Làm mới
        </Button>
      </AdminPageHeader>
      <ErrorBanner message={error} />

      <section className="grid gap-4 grid-cols-1 sm:grid-cols-2 xl:grid-cols-4">
        <DashboardStatCard
          label="Tổng tin nhắn"
          value={data?.total_messages ?? '—'}
          icon={MessageSquare}
          accentClassName="bg-primary/10 text-primary"
          loading={loading}
        />
        <DashboardStatCard
          label="Người dùng duy nhất"
          value={data?.unique_users ?? '—'}
          icon={UsersIcon}
          accentClassName="bg-success/15 text-success"
          loading={loading}
        />
        <DashboardStatCard
          label="Chi phí ước tính (USD)"
          value={data ? `$${data.estimated_total_cost_usd.toFixed(2)}` : '—'}
          icon={DollarSign}
          accentClassName="bg-warning/15 text-warning"
          loading={loading}
        />
        <DashboardStatCard
          label="Cache hit rate"
          value={data ? `${(data.semantic_cache_hit_rate * 100).toFixed(1)}%` : '—'}
          icon={Zap}
          accentClassName="bg-accent text-accent-foreground"
          trendLabel={data ? `${data.semantic_cache_hits} hits / ${data.semantic_cache_entries} entries` : undefined}
          loading={loading}
        />
      </section>

      <section className="grid gap-4 grid-cols-1 lg:grid-cols-2 mt-6">
        <CostByModelCard data={data} loading={loading} />
        <TopQuestionsCard data={data} loading={loading} />
      </section>
    </AdminLayout>
  )
}

function CostByModelCard({ data, loading }: { data: AnalyticsOverview | null; loading: boolean }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Chi phí theo model</CardTitle>
        <CardDescription>Ước tính dựa trên giá Gemini hiện hành</CardDescription>
      </CardHeader>
      <CardContent>
        {loading ? (
          <Skeleton className="h-32 w-full" />
        ) : !data?.cost_by_model.length ? (
          <p className="text-sm text-muted-foreground">Không có dữ liệu trong khoảng thời gian.</p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-xs text-muted-foreground border-b">
                <th className="text-left py-2 font-medium">Model</th>
                <th className="text-right py-2 font-medium">Input tok</th>
                <th className="text-right py-2 font-medium">Output tok</th>
                <th className="text-right py-2 font-medium">USD</th>
              </tr>
            </thead>
            <tbody>
              {data.cost_by_model.map((m) => (
                <tr key={m.model} className="border-b last:border-b-0">
                  <td className="py-2 font-mono text-xs">{m.model}</td>
                  <td className="py-2 text-right tabular-nums">{m.input_tokens.toLocaleString()}</td>
                  <td className="py-2 text-right tabular-nums">{m.output_tokens.toLocaleString()}</td>
                  <td className="py-2 text-right tabular-nums font-medium">${m.estimated_usd.toFixed(4)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </CardContent>
    </Card>
  )
}

function TopQuestionsCard({ data, loading }: { data: AnalyticsOverview | null; loading: boolean }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Câu hỏi phổ biến</CardTitle>
        <CardDescription>Top 10 — group theo nội dung tin nhắn</CardDescription>
      </CardHeader>
      <CardContent>
        {loading ? (
          <Skeleton className="h-32 w-full" />
        ) : !data?.top_questions.length ? (
          <p className="text-sm text-muted-foreground">Chưa có câu hỏi nào.</p>
        ) : (
          <ol className="space-y-2">
            {data.top_questions.map((q, idx) => (
              <li key={idx} className="flex items-start gap-2 text-sm">
                <span className="text-xs font-mono text-muted-foreground mt-0.5 w-5 shrink-0">
                  #{idx + 1}
                </span>
                <span className="flex-1 line-clamp-2">{q.question}</span>
                <span className="text-xs tabular-nums text-muted-foreground shrink-0">×{q.count}</span>
              </li>
            ))}
          </ol>
        )}
      </CardContent>
    </Card>
  )
}
