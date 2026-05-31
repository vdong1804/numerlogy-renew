/**
 * Report detail — /my-account/reports/[id]
 * Shows metadata + input payload + download button.
 */
import { ArrowLeft, Download, FileText } from 'lucide-react'
import Link from 'next/link'
import { useRouter } from 'next/router'
import { useEffect, useState } from 'react'

import AccountLayout from '@/components/my-account/account-layout'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import {
  downloadReportBlob,
  listReports,
  type MyReport,
} from '@/lib/my-account-api'

export default function MyReportDetailPage() {
  const router = useRouter()
  const idParam = router.query.id
  const id = typeof idParam === 'string' ? Number(idParam) : NaN

  const [report, setReport] = useState<MyReport | null>(null)
  const [loading, setLoading] = useState(true)
  const [downloading, setDownloading] = useState(false)
  const [notFound, setNotFound] = useState(false)

  useEffect(() => {
    if (!Number.isFinite(id)) return
    // No dedicated GET /reports/{id}; pull from list by id (cheap, limit=200)
    listReports({ limit: 200 })
      .then((res) => {
        const found = res.items.find((r) => r.id === id)
        if (!found) setNotFound(true)
        else setReport(found)
      })
      .catch(() => setNotFound(true))
      .finally(() => setLoading(false))
  }, [id])

  const handleDownload = async () => {
    if (!report) return
    setDownloading(true)
    try {
      const blob = await downloadReportBlob(report.id)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `report-${report.id}.pdf`
      a.click()
      URL.revokeObjectURL(url)
    } catch {
      // best effort
    } finally {
      setDownloading(false)
    }
  }

  return (
    <AccountLayout title="Chi tiết báo cáo" description="Thông tin & tải lại">
      <div className="mb-4">
        <Link
          href="/my-account/reports"
          className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-primary"
        >
          <ArrowLeft className="w-4 h-4" /> Quay lại thư viện
        </Link>
      </div>

      {loading && <Skeleton className="h-48 w-full rounded-xl" />}

      {!loading && notFound && (
        <div className="rounded-xl border border-border bg-card p-6 text-center">
          <p className="text-sm text-muted-foreground">
            Không tìm thấy báo cáo hoặc bạn không có quyền truy cập.
          </p>
        </div>
      )}

      {!loading && report && (
        <div className="grid grid-cols-1 lg:grid-cols-[1fr_280px] gap-6">
          <article className="rounded-xl border border-border bg-card p-6">
            <div className="flex items-center gap-2 mb-3">
              <FileText className="w-5 h-5 text-primary" />
              <h2 className="text-lg font-semibold">Báo cáo #{report.id}</h2>
            </div>

            <dl className="grid grid-cols-[140px_1fr] text-sm gap-y-2">
              <dt className="text-muted-foreground">Ngày tạo</dt>
              <dd>{formatDate(report.generated_at)}</dd>

              <dt className="text-muted-foreground">Lượt đã tải</dt>
              <dd>{report.download_count}</dd>

              {report.last_downloaded_at && (
                <>
                  <dt className="text-muted-foreground">Tải lần cuối</dt>
                  <dd>{formatDate(report.last_downloaded_at)}</dd>
                </>
              )}

              {report.order_id && (
                <>
                  <dt className="text-muted-foreground">Đơn hàng</dt>
                  <dd>
                    <Link
                      href={`/my-account/orders/${report.order_id}`}
                      className="text-primary hover:underline"
                    >
                      Xem đơn #{report.order_id}
                    </Link>
                  </dd>
                </>
              )}
            </dl>

            {report.input_payload && Object.keys(report.input_payload).length > 0 && (
              <div className="mt-6">
                <h3 className="text-sm font-medium mb-2">Thông tin lấy số</h3>
                <div className="rounded-lg bg-muted/40 p-3 text-xs grid grid-cols-1 sm:grid-cols-2 gap-y-1.5 gap-x-4">
                  {Object.entries(report.input_payload).map(([k, v]) => (
                    <div key={k} className="flex gap-2">
                      <span className="text-muted-foreground capitalize">
                        {humanize(k)}:
                      </span>
                      <span className="font-medium break-all">
                        {String(v ?? '')}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </article>

          <aside className="rounded-xl border border-border bg-card p-6 h-fit">
            <h3 className="text-sm font-semibold mb-3">Tải xuống</h3>
            <p className="text-xs text-muted-foreground mb-4">
              File PDF được lưu vĩnh viễn trong tài khoản của bạn. Tải lại bất cứ lúc nào.
            </p>
            <Button onClick={handleDownload} disabled={downloading} className="w-full">
              <Download className="w-4 h-4" />{' '}
              {downloading ? 'Đang tải...' : 'Tải PDF'}
            </Button>
          </aside>
        </div>
      )}
    </AccountLayout>
  )
}

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleString('vi-VN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    })
  } catch {
    return iso
  }
}

function humanize(key: string): string {
  return key.replace(/_/g, ' ')
}
