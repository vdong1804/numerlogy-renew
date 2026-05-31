/**
 * Dashboard card showing active subscription package details.
 */
import Link from 'next/link'
import { Package as PackageIcon } from 'lucide-react'

interface Props {
  packageName?: string | null
  quotaTotal?: number | null
  acquiredAt?: string | null
  expiresAt?: string | null
}

export default function DashboardPackageCard({
  packageName,
  quotaTotal,
  acquiredAt,
  expiresAt,
}: Props) {
  const empty = !packageName
  const daysLeft = expiresAt ? daysUntil(expiresAt) : null
  const expired = daysLeft != null && daysLeft < 0
  const soon = daysLeft != null && daysLeft >= 0 && daysLeft <= 7

  return (
    <div className="rounded-xl border border-border bg-card p-5">
      <div className="flex items-center justify-between">
        <p className="text-xs uppercase tracking-wide text-muted-foreground">
          Gói đang dùng
        </p>
        <PackageIcon className="w-4 h-4 text-muted-foreground" />
      </div>

      {empty ? (
        <>
          <p className="text-base font-semibold mt-2">Chưa có gói</p>
          <Link
            href="/shop"
            className="inline-block text-xs text-primary hover:underline mt-2"
          >
            → Mua gói tại Cửa hàng
          </Link>
        </>
      ) : (
        <>
          <p className="text-xl font-bold mt-1">{packageName}</p>
          {quotaTotal != null && (
            <p className="text-xs text-muted-foreground mt-1">
              {quotaTotal} lượt tải / gói
            </p>
          )}
          {acquiredAt && (
            <p className="text-xs text-muted-foreground">
              Kích hoạt: {formatDate(acquiredAt)}
            </p>
          )}
          {expiresAt ? (
            <p
              className={
                'text-xs mt-1 ' +
                (expired
                  ? 'text-red-600 font-medium'
                  : soon
                  ? 'text-amber-600 font-medium'
                  : 'text-muted-foreground')
              }
            >
              {expired
                ? `Hết hạn từ ${formatDate(expiresAt)}`
                : `Hết hạn: ${formatDate(expiresAt)}${
                    soon ? ` (còn ${daysLeft} ngày)` : ''
                  }`}
            </p>
          ) : (
            <p className="text-xs text-muted-foreground mt-1">
              Trọn đời (không hết hạn)
            </p>
          )}
        </>
      )}
    </div>
  )
}

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleDateString('vi-VN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
    })
  } catch {
    return iso.slice(0, 10)
  }
}

function daysUntil(iso: string): number | null {
  try {
    const diffMs = new Date(iso).getTime() - Date.now()
    return Math.floor(diffMs / (1000 * 60 * 60 * 24))
  } catch {
    return null
  }
}
