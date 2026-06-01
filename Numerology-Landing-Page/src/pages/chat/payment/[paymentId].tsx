/**
 * /chat/payment/[paymentId] — dedicated payment page for chat add-on purchases.
 *
 * Mirrors the /check-out/[orderId] flow for PDF reports: re-hydrates a
 * UserPayment via GET /api/chat/addons/payments/{id}, renders the unified
 * SePayPaymentBlock, and polls quota for fulfilment. On `paid` → redirect to
 * /chat with a success toast.
 */

import {
  ArrowLeft,
  HeadphonesIcon,
  Phone,
  RefreshCw,
  ShieldCheck,
  XCircle,
} from 'lucide-react'
import Link from 'next/link'
import { useRouter } from 'next/router'
import type { ReactElement } from 'react'
import { useCallback, useEffect, useRef, useState } from 'react'
import { toast } from 'sonner'

import SePayPaymentBlock, {
  type SePayStatus,
} from '@/components/checkout/sepay-payment-block'
import useAddonStatusPoller from '@/components/checkout/use-addon-status-poller'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { Main } from '@/layouts/Main'
import { Meta } from '@/layouts/Meta'
import { useUserAuth } from '@/lib/user-auth'
import { formatVnd } from '@/lib/utils'
import type { NextPageWithLayout } from '@/models'
import {
  type AddonPayment,
  getAddonPayment,
  getQuota,
} from '@/modules/chat/api/chat-api'

const ChatPaymentPage: NextPageWithLayout = () => {
  const { user, loading: authLoading } = useUserAuth()
  const router = useRouter()
  const paymentId = Number(router.query.paymentId)

  const [payment, setPayment] = useState<AddonPayment | null>(null)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const startingAddonRef = useRef(0)

  // Auth guard
  useEffect(() => {
    if (!authLoading && !user) {
      router.replace(
        `/login?next=${encodeURIComponent(`/chat/payment/${paymentId}`)}`
      )
    }
  }, [authLoading, user, router, paymentId])

  // Fetch payment + snapshot starting addon credit for delta detection
  useEffect(() => {
    if (!user || !paymentId || Number.isNaN(paymentId)) return
    setLoading(true)
    Promise.all([getAddonPayment(paymentId), getQuota().catch(() => null)])
      .then(([p, q]) => {
        setPayment(p)
        startingAddonRef.current = q?.addonRemaining ?? 0
      })
      .catch((err) =>
        setLoadError((err as Error).message || 'Không tải được giao dịch')
      )
      .finally(() => setLoading(false))
  }, [user, paymentId])

  const { status: paymentStatus } = useAddonStatusPoller({
    enabled: payment !== null && payment.status === 1,
    startingAddonRemaining: startingAddonRef.current,
    onPaid: () => {
      toast.success('Đã kích hoạt gói! Đang chuyển về Chat AI...')
      setTimeout(() => router.push('/chat'), 1800)
    },
  })

  // Allow user to retry fetch + manually re-check status
  const handleRefresh = useCallback(async () => {
    if (!paymentId) return
    try {
      const fresh = await getAddonPayment(paymentId)
      setPayment(fresh)
      toast.info('Đã làm mới trạng thái')
    } catch (err) {
      toast.error((err as Error).message || 'Không làm mới được')
    }
  }, [paymentId])

  // ---- Loading / error / unauthorised ------------------------------------

  if (authLoading || !user) {
    return (
      <div className="account-shell dark min-h-[60vh] flex items-center justify-center">
        <p className="text-sm text-muted-foreground">Đang tải...</p>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="account-shell dark min-h-[calc(100vh-93px)]">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 py-10 space-y-4">
          <Skeleton className="h-6 w-32" />
          <Skeleton className="h-10 w-72" />
          <Skeleton className="h-96 w-full rounded-2xl" />
        </div>
      </div>
    )
  }

  if (!payment) {
    return (
      <div className="account-shell dark min-h-[calc(100vh-93px)]">
        <div className="max-w-xl mx-auto px-4 py-20 text-center">
          <XCircle className="w-12 h-12 text-muted-foreground mx-auto mb-3" />
          <h1 className="text-xl font-semibold text-foreground">
            Không tìm thấy giao dịch
          </h1>
          {loadError && (
            <p className="text-destructive text-sm mt-3">{loadError}</p>
          )}
          <Button asChild variant="outline" className="mt-6">
            <Link href="/chat/upgrade">
              <ArrowLeft className="w-4 h-4" /> Quay lại danh sách gói
            </Link>
          </Button>
        </div>
      </div>
    )
  }

  // ---- Render -------------------------------------------------------------

  const refCode = `CHATADDON${payment.paymentId}`
  // Server-side terminal status overrides the poller (approved=2 → paid,
  // rejected=3 → failed). For status=1 we trust the poller.
  let overrideStatus: SePayStatus | null = null
  if (payment.status === 2) overrideStatus = 'paid'
  else if (payment.status === 3) overrideStatus = 'failed'
  const effectiveStatus: SePayStatus = overrideStatus ?? paymentStatus

  return (
    <div className="account-shell dark min-h-[calc(100vh-93px)]">
      <div className="max-w-3xl mx-auto px-4 sm:px-6 py-10">
        {/* Back link */}
        <Link
          href="/chat/upgrade"
          className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors mb-5"
        >
          <ArrowLeft className="w-4 h-4" aria-hidden="true" />
          Quay lại danh sách gói
        </Link>

        {/* Header */}
        <header className="mb-6">
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight">
            Thanh toán gói tin nhắn
          </h1>
          <div className="h-[3px] w-12 bg-primary rounded-full mt-2 mb-3" />
          {payment.packageName && (
            <p className="text-sm text-muted-foreground">
              Gói:{' '}
              <span className="font-semibold text-foreground">
                {payment.packageName}
              </span>
              {' · '}
              Tổng tiền:{' '}
              <span className="font-semibold text-foreground">
                {formatVnd(payment.price)}
              </span>
            </p>
          )}
        </header>

        {/* Unified SePay block */}
        <SePayPaymentBlock
          amount={payment.price}
          refCode={refCode}
          status={effectiveStatus}
          isPolling={effectiveStatus === 'pending'}
          footnote={
            <>
              Gói sẽ được kích hoạt tự động trong vài phút sau khi bạn chuyển
              khoản. Bấm{' '}
              <button
                type="button"
                onClick={handleRefresh}
                className="inline-flex items-center gap-1 text-primary hover:underline font-medium"
              >
                <RefreshCw className="w-3 h-3" />
                Làm mới
              </button>{' '}
              nếu trạng thái không tự cập nhật.
            </>
          }
        />

        {/* Support box */}
        <div className="mt-5 rounded-2xl border border-border bg-gradient-to-br from-primary/10 via-card/60 to-card/40 p-4 flex items-start gap-3">
          <span
            aria-hidden="true"
            className="shrink-0 inline-flex items-center justify-center w-10 h-10 rounded-xl bg-primary/20 text-primary"
          >
            <ShieldCheck className="w-5 h-5" />
          </span>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-semibold text-foreground flex items-center gap-1.5">
              <HeadphonesIcon className="w-4 h-4 text-primary" />
              Cần hỗ trợ?
            </p>
            <p className="text-xs text-muted-foreground mt-0.5 leading-relaxed">
              Nếu giao dịch không tự cập nhật sau vài phút, vui lòng gọi hotline
              để được kích hoạt thủ công.
            </p>
            <a
              href="tel:0339387373"
              className="mt-2 inline-flex items-center gap-1.5 text-sm font-semibold text-primary hover:underline"
            >
              <Phone className="w-4 h-4" />
              0339 387 373
            </a>
          </div>
        </div>
      </div>
    </div>
  )
}

ChatPaymentPage.getLayout = function getLayout(page: ReactElement) {
  return (
    <Main
      meta={
        <Meta
          title="Thanh toán gói Chat AI · Numerology"
          description="Hoàn tất thanh toán gói tin nhắn"
        />
      }
    >
      {page}
    </Main>
  )
}

export default ChatPaymentPage
