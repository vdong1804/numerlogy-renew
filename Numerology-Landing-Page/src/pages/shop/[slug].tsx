/**
 * Product detail page — /shop/[slug]
 *
 * Two flows:
 *  - type=package or combo  -> "Mua ngay" creates order with no input_payload
 *  - type=report            -> shows a form (name, birth_day, phone, gender)
 *                              -> POST /orders { items, input_payload }
 *
 * On success the user is redirected to /check-out/[orderId].
 */
import Link from 'next/link'
import { useRouter } from 'next/router'
import {
  ArrowLeft,
  CheckCircle2,
  FileText,
  Layers,
  Package,
  ShieldCheck,
  XCircle,
} from 'lucide-react'
import { useEffect, useState } from 'react'
import type { ReactElement } from 'react'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { NativeSelect } from '@/components/ui/native-select'
import { Skeleton } from '@/components/ui/skeleton'
import { Main } from '@/layouts/Main'
import { Meta } from '@/layouts/Meta'
import { createOrder, getProductBySlug, type Product } from '@/lib/shop-api'
import { formatVnd } from '@/lib/utils'
import type { NextPageWithLayout } from '@/models'

interface ReportInput {
  name: string
  birth_day: string
  phone: string
  gender: 'male' | 'female' | ''
}

const TYPE_LABEL: Record<Product['type'], string> = {
  package: 'Gói thuê bao',
  report: 'Báo cáo lẻ',
  combo: 'Combo ưu đãi',
}

const TYPE_ICON: Record<Product['type'], typeof Package> = {
  package: Package,
  report: FileText,
  combo: Layers,
}

const FIELD_CLS = 'h-10 bg-muted/40'

const ProductDetailPage: NextPageWithLayout = () => {
  const router = useRouter()
  const slug = router.query.slug as string | undefined

  const [product, setProduct] = useState<Product | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [form, setForm] = useState<ReportInput>({
    name: '',
    birth_day: '',
    phone: '',
    gender: '',
  })

  useEffect(() => {
    if (!slug) return
    setLoading(true)
    getProductBySlug(slug)
      .then(setProduct)
      .catch((err) => setError((err as Error).message))
      .finally(() => setLoading(false))
  }, [slug])

  const handleBuy = async () => {
    if (!product) return
    setSubmitting(true)
    setError('')
    try {
      const isReport = product.type === 'report'
      if (isReport && (!form.name || !form.birth_day)) {
        setError('Vui lòng nhập đầy đủ Họ tên và Ngày sinh')
        setSubmitting(false)
        return
      }
      const order = await createOrder({
        items: [{ product_id: product.id, qty: 1 }],
        input_payload: isReport ? { ...form } : {},
      })
      // Free orders are paid + fulfilled server-side — skip the QR checkout.
      if (order.status === 'paid' || order.total_amount === 0) {
        const target = isReport ? '/my-account/reports' : '/my-account'
        router.push(target)
        return
      }
      router.push(`/check-out/${order.id}`)
    } catch (err) {
      setError((err as Error).message)
      setSubmitting(false)
    }
  }

  if (loading) {
    return (
      <div className="account-shell min-h-[70vh]">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 py-8 space-y-4">
          <Skeleton className="h-6 w-32" />
          <Skeleton className="h-10 w-72" />
          <div className="grid grid-cols-1 lg:grid-cols-[1fr_360px] gap-6">
            <Skeleton className="h-64 w-full rounded-xl" />
            <Skeleton className="h-64 w-full rounded-xl" />
          </div>
        </div>
      </div>
    )
  }

  if (!product) {
    return (
      <div className="account-shell min-h-[70vh]">
        <div className="max-w-2xl mx-auto px-4 py-16 text-center">
          <XCircle className="w-12 h-12 text-muted-foreground mx-auto mb-3" />
          <h1 className="text-xl font-semibold">Không tìm thấy sản phẩm</h1>
          {error && (
            <p className="text-destructive text-sm mt-3">{error}</p>
          )}
          <Button asChild variant="outline" className="mt-6">
            <Link href="/shop">
              <ArrowLeft className="w-4 h-4" /> Quay lại Cửa hàng
            </Link>
          </Button>
        </div>
      </div>
    )
  }

  const free = product.price === 0
  const isReport = product.type === 'report'
  const TypeIcon = TYPE_ICON[product.type]

  return (
    <div className="account-shell min-h-[70vh]">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 py-8">
        {/* Breadcrumb */}
        <Link
          href="/shop"
          className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors mb-4"
        >
          <ArrowLeft className="w-4 h-4" /> Quay lại Cửa hàng
        </Link>

        {/* Title row */}
        <header className="mb-6">
          <Badge variant="outline" className="mb-2 inline-flex items-center gap-1.5">
            <TypeIcon className="w-3.5 h-3.5" />
            {TYPE_LABEL[product.type]}
          </Badge>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-foreground">
            {product.name}
          </h1>
          <div className="h-[3px] w-12 bg-primary rounded-full mt-2" />
          {product.description && (
            <p className="text-sm sm:text-base text-muted-foreground mt-2 max-w-2xl">
              {product.description}
            </p>
          )}
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-[1fr_360px] gap-6">
          {/* LEFT — product info / report input form */}
          <div className="space-y-6">
            {/* Highlights card (visible for all types) */}
            <div className="rounded-2xl border border-border bg-card shadow-sm p-5 sm:p-6">
              <h2 className="font-semibold mb-3 flex items-center gap-2">
                <span className="inline-block w-1.5 h-1.5 rounded-full bg-primary shadow-[0_0_8px_rgba(249,106,45,0.6)]" />
                Bạn nhận được gì
              </h2>
              <ul className="space-y-2 text-sm">
                {(product.type === 'package' || product.type === 'combo') &&
                  product.quota != null && (
                    <FeatureRow text={`${product.quota} báo cáo trong gói`} />
                  )}
                {product.type === 'package' && product.renewal_days ? (
                  <FeatureRow
                    text={`Hiệu lực ${product.renewal_days} ngày kể từ khi kích hoạt`}
                  />
                ) : null}
                {product.type === 'report' && (
                  <FeatureRow text="Báo cáo PDF chi tiết, có thể tải về và lưu trữ" />
                )}
                <FeatureRow text="Bảo mật thông tin cá nhân tuyệt đối" />
              </ul>
            </div>

            {/* Report-only form card */}
            {isReport && (
              <div className="rounded-2xl border border-border bg-card shadow-sm overflow-hidden">
                <div className="flex items-center gap-2.5 border-b border-border bg-gradient-to-r from-primary/8 via-muted/30 to-secondary/10 px-5 sm:px-6 py-3.5">
                  <span className="inline-flex items-center justify-center w-8 h-8 rounded-full bg-primary/10 text-primary">
                    <FileText className="w-4 h-4" />
                  </span>
                  <div>
                    <h2 className="font-semibold leading-tight">Thông tin lá số</h2>
                    <p className="text-xs text-muted-foreground">
                      Báo cáo sẽ được tính dựa trên dữ liệu này — kiểm tra kỹ trước khi gửi.
                    </p>
                  </div>
                </div>
                <div className="px-5 sm:px-6 py-5 grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="sm:col-span-2 space-y-1.5">
                    <Label htmlFor="name">
                      Họ và tên <span className="text-destructive">*</span>
                    </Label>
                    <Input
                      id="name"
                      autoComplete="name"
                      value={form.name}
                      onChange={(e) => setForm({ ...form, name: e.target.value })}
                      placeholder="Nguyễn Văn A"
                      className={FIELD_CLS}
                    />
                  </div>
                  <div className="space-y-1.5">
                    <Label htmlFor="birth_day">
                      Ngày sinh <span className="text-destructive">*</span>
                    </Label>
                    <Input
                      id="birth_day"
                      type="date"
                      autoComplete="bday"
                      value={form.birth_day}
                      onChange={(e) =>
                        setForm({ ...form, birth_day: e.target.value })
                      }
                      className={FIELD_CLS}
                    />
                  </div>
                  <div className="space-y-1.5">
                    <Label htmlFor="phone">Số điện thoại</Label>
                    <Input
                      id="phone"
                      type="tel"
                      inputMode="tel"
                      autoComplete="tel"
                      value={form.phone}
                      onChange={(e) =>
                        setForm({ ...form, phone: e.target.value })
                      }
                      placeholder="09xxxxxxxx"
                      className={FIELD_CLS}
                    />
                  </div>
                  <div className="sm:col-span-2 space-y-1.5">
                    <Label htmlFor="gender">Giới tính</Label>
                    <NativeSelect
                      id="gender"
                      value={form.gender}
                      onChange={(e) =>
                        setForm({
                          ...form,
                          gender: e.target.value as ReportInput['gender'],
                        })
                      }
                      className="h-10 bg-muted/40"
                    >
                      <option value="">Chưa chọn</option>
                      <option value="male">Nam</option>
                      <option value="female">Nữ</option>
                    </NativeSelect>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* RIGHT — sticky order summary */}
          <aside className="lg:sticky lg:top-24 lg:self-start">
            <div className="rounded-2xl border border-border bg-card shadow-md overflow-hidden">
              <div className="px-5 py-4 border-b border-border bg-gradient-to-br from-primary/10 to-secondary/10">
                <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                  Tổng thanh toán
                </p>
                <div className="mt-1 flex items-baseline gap-2">
                  <span className="text-3xl font-bold text-foreground">
                    {free ? 'Miễn phí' : formatVnd(product.price)}
                  </span>
                  {!free && product.type === 'package' && (
                    <span className="text-xs text-muted-foreground">/ chu kỳ</span>
                  )}
                </div>
              </div>

              <div className="px-5 py-4 text-sm text-muted-foreground space-y-1.5">
                <p className="flex items-center justify-between">
                  <span>Loại sản phẩm</span>
                  <span className="text-foreground font-medium">
                    {TYPE_LABEL[product.type]}
                  </span>
                </p>
                {product.quota != null && (
                  <p className="flex items-center justify-between">
                    <span>Số báo cáo</span>
                    <span className="text-foreground font-medium">
                      {product.quota}
                    </span>
                  </p>
                )}
                {product.renewal_days ? (
                  <p className="flex items-center justify-between">
                    <span>Thời hạn</span>
                    <span className="text-foreground font-medium">
                      {product.renewal_days} ngày
                    </span>
                  </p>
                ) : null}
              </div>

              {error && (
                <div className="mx-5 mb-3 flex items-start gap-2 rounded-md border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive">
                  <XCircle className="w-4 h-4 mt-0.5 shrink-0" />
                  <span>{error}</span>
                </div>
              )}

              <div className="px-5 pb-5">
                <Button
                  size="lg"
                  className="w-full"
                  onClick={handleBuy}
                  disabled={submitting}
                >
                  {submitting
                    ? 'Đang tạo đơn...'
                    : free
                    ? 'Nhận miễn phí'
                    : 'Mua ngay'}
                </Button>
                <p className="text-xs text-muted-foreground text-center mt-3 flex items-center justify-center gap-1.5">
                  <ShieldCheck className="w-3.5 h-3.5" />
                  Thanh toán an toàn qua VietQR
                </p>
              </div>
            </div>
          </aside>
        </div>
      </div>
    </div>
  )
}

function FeatureRow({ text }: { text: string }) {
  return (
    <li className="flex items-start gap-2.5">
      <CheckCircle2 className="w-4 h-4 text-primary shrink-0 mt-0.5" />
      <span className="text-foreground/90">{text}</span>
    </li>
  )
}

ProductDetailPage.getLayout = function getLayout(page: ReactElement) {
  return (
    <Main meta={<Meta title="Chi tiết sản phẩm" description="Mua báo cáo Thần Số Học" />}>
      {page}
    </Main>
  )
}

export default ProductDetailPage
