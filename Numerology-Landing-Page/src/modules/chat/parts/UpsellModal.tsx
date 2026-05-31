/**
 * UpsellModal — shown when quota is exhausted (402 REST or SSE quota_exceeded).
 * Lists addon packages inline. "Mua ngay" initiates purchase and shows bank
 * transfer info inline. "Để mai" closes without action.
 */

import { useRouter } from 'next/router'
import { useCallback, useEffect, useState } from 'react'
import { toast } from 'sonner'

import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { cn, formatVnd } from '@/lib/utils'
import type { AddonPurchaseInitiate } from '@/models/Chat'

import { getQuota, purchaseAddon } from '../api/chat-api'
import AddonList from '../upgrade/AddonList'

// ---------------------------------------------------------------------------
// Sub-component
// ---------------------------------------------------------------------------

function Row({
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
    <div className="flex items-center justify-between gap-2">
      <span className="text-muted-foreground shrink-0">{label}</span>
      <span
        className={cn(
          'text-right',
          mono && 'font-mono',
          bold && 'font-semibold text-primary'
        )}
      >
        {value}
      </span>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Modal
// ---------------------------------------------------------------------------

interface UpsellModalProps {
  open: boolean
  onClose: () => void
}

export default function UpsellModal({ open, onClose }: UpsellModalProps) {
  const router = useRouter()
  const [purchasingId, setPurchasingId] = useState<number | null>(null)
  const [purchaseInfo, setPurchaseInfo] =
    useState<AddonPurchaseInitiate | null>(null)
  const [purchaseError, setPurchaseError] = useState<string | null>(null)

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
    try {
      const info = await purchaseAddon(packageId)
      setPurchaseInfo(info)
    } catch (err) {
      setPurchaseError(
        (err as Error).message || 'Không thể khởi tạo thanh toán'
      )
    } finally {
      setPurchasingId(null)
    }
  }, [])

  const handleGoUpgrade = () => {
    onClose()
    router.push('/chat/upgrade')
  }

  const handleClose = () => {
    setPurchaseInfo(null)
    setPurchaseError(null)
    onClose()
  }

  return (
    <Dialog
      open={open}
      onOpenChange={(v) => {
        if (!v) handleClose()
      }}
    >
      <DialogContent
        className="max-w-lg w-full"
        aria-labelledby="upsell-title"
        aria-describedby="upsell-desc"
      >
        <DialogHeader>
          <DialogTitle id="upsell-title">
            Bạn đã hết lượt nhắn tin miễn phí hôm nay
          </DialogTitle>
          <DialogDescription id="upsell-desc">
            Mua thêm gói tin nhắn để tiếp tục trò chuyện với Trợ lý AI.
          </DialogDescription>
        </DialogHeader>

        {/* Bank transfer info after purchase initiated */}
        {purchaseInfo ? (
          <div className="space-y-3">
            <p className="text-sm font-medium text-foreground">
              Chuyển khoản để hoàn tất thanh toán:
            </p>
            <div className="rounded-lg border border-border bg-muted/40 p-4 text-sm space-y-1.5">
              <Row label="Ngân hàng" value={purchaseInfo.bankName} />
              <Row label="Mã ngân hàng" value={purchaseInfo.bankCode} mono />
              <Row
                label="Số tài khoản"
                value={purchaseInfo.bankAccountNumber}
                mono
              />
              <Row
                label="Chủ tài khoản"
                value={purchaseInfo.bankAccountHolder}
              />
              <Row label="Số tiền" value={formatVnd(purchaseInfo.price)} bold />
              <Row
                label="Nội dung CK"
                value={`CHATADDON${purchaseInfo.paymentId}`}
                mono
              />
            </div>
            <p className="text-xs text-muted-foreground">
              Gói tin nhắn sẽ được kích hoạt sau khi xác nhận thanh toán (thường
              trong vài phút).
            </p>
            <Button
              className="w-full"
              onClick={handleClose}
              aria-label="Đóng hộp thoại"
            >
              Đã hiểu, đóng lại
            </Button>
          </div>
        ) : (
          <>
            {purchaseError && (
              <p
                role="alert"
                className="text-sm text-destructive rounded-md bg-destructive/10 px-3 py-2"
              >
                {purchaseError}
              </p>
            )}

            {/* Inline addon list — capped at 3 cheapest options (M6) */}
            <div className="max-h-72 overflow-y-auto pr-1">
              <AddonList
                onPurchase={handlePurchase}
                purchasingId={purchasingId}
                limit={3}
              />
            </div>

            <DialogFooter className="flex-col sm:flex-row gap-2 pt-2">
              <Button
                variant="outline"
                onClick={handleClose}
                aria-label="Để mai, đóng hộp thoại"
                className="w-full sm:w-auto"
              >
                Để mai
              </Button>
              <Button
                variant="ghost"
                onClick={handleGoUpgrade}
                aria-label="Xem tất cả gói tin nhắn"
                className="w-full sm:w-auto text-muted-foreground"
              >
                Xem tất cả gói
              </Button>
            </DialogFooter>
          </>
        )}
      </DialogContent>
    </Dialog>
  )
}
