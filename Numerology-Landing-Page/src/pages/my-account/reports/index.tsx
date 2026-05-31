/**
 * Reports library — /my-account/reports
 */
import DescriptionOutlinedIcon from '@mui/icons-material/DescriptionOutlined'
import { Download, FileText } from 'lucide-react'
import { useEffect, useState } from 'react'

import AccountLayout from '@/components/my-account/account-layout'
import EmptyState from '@/components/empty-state'
import ReportCardSkeleton from '@/components/skeleton/report-card-skeleton'
import { Button } from '@/components/ui/button'
import {
  downloadReportBlob,
  listReports,
  type MyReport,
} from '@/lib/my-account-api'

export default function MyReportsPage() {
  const [reports, setReports] = useState<MyReport[]>([])
  const [loading, setLoading] = useState(true)
  const [downloading, setDownloading] = useState<number | null>(null)

  useEffect(() => {
    listReports({ limit: 50 })
      .then((res) => setReports(res.items))
      .catch(() => undefined)
      .finally(() => setLoading(false))
  }, [])

  const handleDownload = async (r: MyReport) => {
    setDownloading(r.id)
    try {
      const blob = await downloadReportBlob(r.id)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `report-${r.id}.pdf`
      a.click()
      URL.revokeObjectURL(url)
    } catch {
      // best effort
    } finally {
      setDownloading(null)
    }
  }

  return (
    <AccountLayout title="Báo cáo của tôi" description="Tải lại bất cứ lúc nào">
      {loading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <ReportCardSkeleton key={i} />
          ))}
        </div>
      ) : reports.length === 0 ? (
        <EmptyState
          icon={<DescriptionOutlinedIcon fontSize="inherit" />}
          title="Chưa có báo cáo nào"
          description="Mua báo cáo thần số học đầu tiên của bạn và nhận ngay trong vài phút."
          ctaLabel="Đến trang Cửa hàng"
          ctaHref="/shop"
        />
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {reports.map((r) => (
            <div key={r.id} className="rounded-xl border border-border bg-card p-4">
              <FileText className="w-6 h-6 text-primary mb-2" />
              <p className="font-medium">Báo cáo #{r.id}</p>
              <p className="text-xs text-muted-foreground mb-3">
                {new Date(r.generated_at).toLocaleString('vi-VN')}
                {r.download_count > 0 && ` · ${r.download_count} lần tải`}
              </p>
              <Button
                size="sm"
                onClick={() => handleDownload(r)}
                disabled={downloading === r.id}
              >
                <Download className="w-3.5 h-3.5" />{' '}
                {downloading === r.id ? 'Đang tải...' : 'Tải PDF'}
              </Button>
            </div>
          ))}
        </div>
      )}
    </AccountLayout>
  )
}
