/**
 * /chat/upgrade — addon package listing page.
 * Auth-guarded: redirects to /login if not authenticated.
 * On purchase: shows inline bank transfer info.
 *
 * Wrapped in `.account-shell.dark` so shadcn-style HSL CSS variables resolve
 * to the dark theme that matches the chat workspace identity.
 */

import {
  ArrowLeft,
  Bot,
  HeadphonesIcon,
  MessageCircle,
  ShieldCheck,
  Sparkles,
  Zap,
} from 'lucide-react'
import Link from 'next/link'
import { useRouter } from 'next/router'
import type { ReactElement } from 'react'
import { useCallback, useEffect, useState } from 'react'

import { Main } from '@/layouts/Main'
import { Meta } from '@/layouts/Meta'
import { useUserAuth } from '@/lib/user-auth'
import type { NextPageWithLayout } from '@/models'
import { purchaseAddon } from '@/modules/chat/api/chat-api'
import AddonList from '@/modules/chat/upgrade/AddonList'

// ---------------------------------------------------------------------------
// Static content — value props + FAQ
// ---------------------------------------------------------------------------

const VALUE_PROPS = [
  {
    icon: Zap,
    title: 'Trả lời nhanh hơn',
    text: 'Ưu tiên xử lý — phản hồi trong vài giây cho mỗi câu hỏi.',
  },
  {
    icon: Bot,
    title: 'Phân tích chuyên sâu',
    text: 'Gói Pro mở khoá mô hình mạnh hơn với khả năng giải nghĩa chi tiết.',
  },
  {
    icon: ShieldCheck,
    title: 'An toàn & riêng tư',
    text: 'Toàn bộ hội thoại được mã hoá. Bạn có thể xoá bất cứ lúc nào.',
  },
]

const FAQS = [
  {
    q: 'Gói tin nhắn có thời hạn không?',
    a: 'Mỗi gói có thời hạn riêng (in trên thẻ gói). Hết hạn, tin nhắn còn lại sẽ không cộng dồn sang gói mới.',
  },
  {
    q: 'Sự khác biệt giữa gói Flash và Pro?',
    a: 'Flash phù hợp cho hỏi đáp nhanh. Pro dùng mô hình mạnh hơn, trả lời chi tiết và phân tích chuyên sâu — phù hợp khi cần giải nghĩa biểu đồ thần số học.',
  },
  {
    q: 'Tôi thanh toán bằng cách nào?',
    a: 'Chuyển khoản ngân hàng theo thông tin hiển thị sau khi bấm "Mua ngay". Hệ thống tự động kích hoạt sau khi nhận được tiền (thường trong vài phút).',
  },
  {
    q: 'Có thể hoàn tiền không?',
    a: 'Hỗ trợ hoàn tiền theo chính sách. Liên hệ hotline 0339 387 373 để được tư vấn.',
  },
]

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function ValuePropCard({
  icon: Icon,
  title,
  text,
}: {
  icon: typeof Zap
  title: string
  text: string
}) {
  return (
    <div className="rounded-xl border border-border bg-card/60 p-4 hover:border-primary/30 transition-colors">
      <div className="w-9 h-9 rounded-lg bg-primary/15 text-primary flex items-center justify-center mb-3">
        <Icon className="w-4.5 h-4.5" aria-hidden="true" />
      </div>
      <h3 className="font-semibold text-sm text-foreground mb-1">{title}</h3>
      <p className="text-xs text-muted-foreground leading-relaxed">{text}</p>
    </div>
  )
}

function FaqItem({ q, a }: { q: string; a: string }) {
  return (
    <details className="group rounded-xl border border-border bg-card/60 px-4 py-3 transition-colors hover:border-primary/30 open:border-primary/40">
      <summary className="flex cursor-pointer items-center justify-between gap-3 text-sm font-medium text-foreground list-none">
        <span>{q}</span>
        <span
          aria-hidden="true"
          className="shrink-0 inline-flex items-center justify-center w-5 h-5 rounded-full bg-muted text-muted-foreground group-open:bg-primary/20 group-open:text-primary transition-colors"
        >
          <svg
            className="w-3 h-3 transition-transform group-open:rotate-180"
            viewBox="0 0 12 12"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <polyline points="3 5 6 8 9 5" />
          </svg>
        </span>
      </summary>
      <p className="mt-2.5 text-xs text-muted-foreground leading-relaxed">
        {a}
      </p>
    </details>
  )
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

const ChatUpgradePage: NextPageWithLayout = () => {
  const { user, loading } = useUserAuth()
  const router = useRouter()
  const [purchasingId, setPurchasingId] = useState<number | null>(null)
  const [purchaseError, setPurchaseError] = useState<string | null>(null)

  useEffect(() => {
    if (!loading && !user) {
      router.replace(`/login?next=${encodeURIComponent('/chat/upgrade')}`)
    }
  }, [loading, user, router])

  /**
   * On purchase: create the pending UserPayment, then navigate to the dedicated
   * /chat/payment/[paymentId] page where the user completes the SePay transfer
   * and watches for fulfilment.
   */
  const handlePurchase = useCallback(
    async (packageId: number) => {
      setPurchasingId(packageId)
      setPurchaseError(null)
      try {
        const info = await purchaseAddon(packageId)
        router.push(`/chat/payment/${info.paymentId}`)
      } catch (err) {
        setPurchaseError(
          (err as Error).message || 'Không thể khởi tạo thanh toán'
        )
      } finally {
        setPurchasingId(null)
      }
    },
    [router]
  )

  if (loading || !user) {
    return (
      <div className="account-shell dark min-h-[60vh] flex items-center justify-center">
        <p className="text-sm text-muted-foreground">Đang tải...</p>
      </div>
    )
  }

  return (
    <div className="account-shell dark min-h-[calc(100vh-93px)]">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 py-10">
        {/* Back link */}
        <Link
          href="/chat"
          className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors mb-6"
        >
          <ArrowLeft className="w-4 h-4" aria-hidden="true" />
          Quay lại Chat AI
        </Link>

        {/* Hero */}
        <header className="mb-10 flex flex-col items-center text-center">
          <span
            aria-hidden="true"
            className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-gradient-to-br from-primary/30 to-primary/10 border border-primary/30 text-primary mb-4 shadow-lg shadow-primary/10"
          >
            <Sparkles className="w-7 h-7" />
          </span>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight">
            Nâng cấp Chat AI
          </h1>
          <p className="mt-3 text-sm sm:text-base text-muted-foreground max-w-xl leading-relaxed">
            Mua thêm gói tin nhắn để trò chuyện không giới hạn với Trợ lý AI
            Numerology. Gói{' '}
            <span className="text-foreground font-semibold">Pro</span> mang lại
            câu trả lời chi tiết với khả năng phân tích chuyên sâu.
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
        <section className="mb-12">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-base font-semibold text-foreground">
              Chọn gói phù hợp
            </h2>
            <span className="text-xs text-muted-foreground inline-flex items-center gap-1">
              <Zap className="w-3 h-3 text-primary" aria-hidden="true" />
              Kích hoạt tự động
            </span>
          </div>
          <AddonList onPurchase={handlePurchase} purchasingId={purchasingId} />
        </section>

        {/* Value props */}
        <section className="mb-12">
          <h2 className="text-base font-semibold text-foreground mb-4">
            Vì sao nên nâng cấp?
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {VALUE_PROPS.map((vp) => (
              <ValuePropCard
                key={vp.title}
                icon={vp.icon}
                title={vp.title}
                text={vp.text}
              />
            ))}
          </div>
        </section>

        {/* FAQ */}
        <section className="mb-12">
          <h2 className="text-base font-semibold text-foreground mb-4">
            Câu hỏi thường gặp
          </h2>
          <div className="space-y-2.5">
            {FAQS.map((f) => (
              <FaqItem key={f.q} q={f.q} a={f.a} />
            ))}
          </div>
        </section>

        {/* Contact banner */}
        <section className="rounded-2xl border border-border bg-gradient-to-br from-primary/10 via-card/60 to-card/40 px-5 py-5 sm:px-6 sm:py-6 flex flex-col sm:flex-row items-start sm:items-center gap-4">
          <span
            aria-hidden="true"
            className="shrink-0 inline-flex items-center justify-center w-11 h-11 rounded-xl bg-primary/20 text-primary"
          >
            <HeadphonesIcon className="w-5 h-5" />
          </span>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-semibold text-foreground">
              Cần tư vấn chọn gói?
            </p>
            <p className="text-xs text-muted-foreground mt-0.5">
              Liên hệ hotline để được hỗ trợ chọn gói phù hợp với nhu cầu của
              bạn.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <a
              href="tel:0339387373"
              className="inline-flex items-center gap-1.5 rounded-full bg-primary text-primary-foreground px-4 py-2 text-xs font-medium hover:bg-primary/90 transition-colors"
            >
              <MessageCircle className="w-3.5 h-3.5" aria-hidden="true" />
              0339 387 373
            </a>
            <Link
              href="/contact"
              className="inline-flex items-center rounded-full border border-border bg-card px-4 py-2 text-xs font-medium text-foreground hover:border-primary/40 hover:text-primary transition-colors"
            >
              Gửi liên hệ
            </Link>
          </div>
        </section>
      </div>
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
