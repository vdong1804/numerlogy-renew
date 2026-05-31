/**
 * /chat/upgrade — addon package listing page.
 * Auth-guarded: redirects to /login if not authenticated.
 * On purchase: shows inline bank transfer info.
 */

import { ArrowLeft } from 'lucide-react'
import Link from 'next/link'
import { useRouter } from 'next/router'
import type { ReactElement } from 'react'
import { useCallback, useEffect, useState } from 'react'
import { toast } from 'sonner'

import { Main } from '@/layouts/Main'
import { Meta } from '@/layouts/Meta'
import { useUserAuth } from '@/lib/user-auth'
import { formatVnd } from '@/lib/utils'
import type { NextPageWithLayout } from '@/models'
import type { AddonPurchaseInitiate } from '@/models/Chat'
import { getQuota, purchaseAddon } from '@/modules/chat/api/chat-api'
import AddonList from '@/modules/chat/upgrade/AddonList'

// ---------------------------------------------------------------------------
// Sub-component
// ---------------------------------------------------------------------------

function InfoRow({
  label,
  value,
  mono = false,
  bold = false,
}: {
  label: string
  value: string
  mono?: boolean
  bold?: boolean
}) {
  return (
    <div className="flex items-center justify-between gap-2 py-1.5 border-b border-border last:border-0">
      <span className="text-muted-foreground shrink-0">{label}</span>
      <span
        className={[
          'text-right',
          mono ? 'font-mono' : '',
          bold ? 'font-semibold text-primary' : 'text-foreground',
        ]
          .filter(Boolean)
          .join(' ')}
      >
        {value}
      </span>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

const ChatUpgradePage: NextPageWithLayout = () => {
  const { user, loading } = useUserAuth()
  const router = useRouter()
  const [purchasingId, setPurchasingId] = useState<number | null>(null)
  const [purchaseInfo, setPurchaseInfo] =
    useState<AddonPurchaseInitiate | null>(null)
  const [purchaseError, setPurchaseError] = useState<string | null>(null)

  useEffect(() => {
    if (!loading && !user) {
      router.replace(`/login?next=${encodeURIComponent('/chat/upgrade')}`)
    }
  }, [loading, user, router])

  // H3 — poll quota every 10s while bank-transfer info is displayed.
  // Stop when addon_remaining > 0 (fulfilled) or after 5-min timeout.
  useEffect(() => {
    if (!purchaseInfo) return undefined
    const startedAt = Date.now()
    let timer: ReturnType<typeof setTimeout>
    const tick = async () => {
      let fulfilled = false
      try {
        const q = await getQuota()
        fulfilled = q.addonRemaining > 0
      } catch {
        // ignore transient errors — keep polling
      }
      if (fulfilled) {
        setPurchaseInfo(null)
        toast.success('Đã kích hoạt gói addon!')
      } else if (Date.now() - startedAt > 5 * 60 * 1000) {
        toast.warning('Vẫn đang xử lý. Vui lòng kiểm tra Lịch sử thanh toán.')
        setPurchaseInfo(null)
      } else {
        timer = setTimeout(tick, 10000)
      }
    }
    timer = setTimeout(tick, 10000)
    return () => clearTimeout(timer)
  }, [purchaseInfo])

  const handlePurchase = useCallback(async (packageId: number) => {
    setPurchasingId(packageId)
    setPurchaseError(null)
    setPurchaseInfo(null)
    try {
      const info = await purchaseAddon(packageId)
      setPurchaseInfo(info)
      setTimeout(() => {
        document
          .getElementById('payment-info')
          ?.scrollIntoView({ behavior: 'smooth' })
      }, 100)
    } catch (err) {
      setPurchaseError(
        (err as Error).message || 'Không thể khởi tạo thanh toán'
      )
    } finally {
      setPurchasingId(null)
    }
  }, [])

  if (loading || !user) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <p className="text-sm text-muted-foreground">Đang tải...</p>
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-8">
      {/* Back link */}
      <Link
        href="/chat"
        className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors mb-6"
      >
        <ArrowLeft className="w-4 h-4" aria-hidden="true" />
        Quay lại Chat AI
      </Link>

      {/* Heading */}
      <header className="mb-8">
        <h1 className="text-2xl sm:text-3xl font-bold tracking-tight">
          Nâng cấp Chat AI
        </h1>
        <div className="h-[3px] w-12 bg-primary rounded-full mt-2 mb-3" />
        <p className="text-sm text-muted-foreground max-w-xl">
          Mua thêm gói tin nhắn để trò chuyện không giới hạn với Trợ lý AI
          Numerology. Gói Pro mang lại câu trả lời chi tiết hơn với khả năng
          phân tích chuyên sâu.
        </p>
      </header>

      {/* Error banner */}
      {purchaseError && (
        <div
          role="alert"
          className="mb-6 rounded-lg bg-destructive/10 border border-destructive/20 px-4 py-3 text-sm text-destructive"
        >
          {purchaseError}
        </div>
      )}

      {/* Addon grid */}
      <AddonList onPurchase={handlePurchase} purchasingId={purchasingId} />

      {/* Payment info — shown after purchase initiated */}
      {purchaseInfo && (
        <div
          id="payment-info"
          className="mt-8 rounded-xl border border-border bg-card p-5 max-w-md"
        >
          <h2 className="font-semibold text-base mb-4">
            Thông tin chuyển khoản
          </h2>
          <div className="space-y-2 text-sm">
            <InfoRow label="Ngân hàng" value={purchaseInfo.bankName} />
            <InfoRow label="Mã ngân hàng" value={purchaseInfo.bankCode} mono />
            <InfoRow
              label="Số tài khoản"
              value={purchaseInfo.bankAccountNumber}
              mono
            />
            <InfoRow
              label="Chủ tài khoản"
              value={purchaseInfo.bankAccountHolder}
            />
            <InfoRow
              label="Số tiền"
              value={formatVnd(purchaseInfo.price)}
              bold
            />
            <InfoRow
              label="Nội dung CK"
              value={`CHATADDON${purchaseInfo.paymentId}`}
              mono
            />
          </div>
          <p className="mt-4 text-xs text-muted-foreground">
            Gói tin nhắn sẽ được kích hoạt sau khi xác nhận thanh toán (thường
            trong vài phút). Liên hệ{' '}
            <a
              href="tel:0339387373"
              className="text-primary hover:underline font-medium"
            >
              0339 387 373
            </a>{' '}
            nếu cần hỗ trợ.
          </p>
        </div>
      )}
    </div>
  )
}

ChatUpgradePage.getLayout = function getLayout(page: ReactElement) {
  return (
    <Main
      meta={
        <Meta
          title="Nâng cấp Chat AI · Numerology"
          description="Mua thêm gói tin nhắn Chat AI"
        />
      }
    >
      {page}
    </Main>
  )
}

export default ChatUpgradePage
