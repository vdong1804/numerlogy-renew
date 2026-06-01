/**
 * UpsellModal — shown when quota is exhausted (402 REST or SSE quota_exceeded).
 * Lists addon packages inline. On "Mua ngay" → closes the modal and routes
 * the user to the dedicated /chat/payment/[id] page (single source of truth
 * for the SePay transfer UI).
 */

import { useRouter } from 'next/router'
import { useCallback, useState } from 'react'

import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'

import { purchaseAddon } from '../api/chat-api'
import AddonList from '../upgrade/AddonList'

interface UpsellModalProps {
  open: boolean
  onClose: () => void
}

export default function UpsellModal({ open, onClose }: UpsellModalProps) {
  const router = useRouter()
  const [purchasingId, setPurchasingId] = useState<number | null>(null)
  const [purchaseError, setPurchaseError] = useState<string | null>(null)

  const handlePurchase = useCallback(
    async (packageId: number) => {
      setPurchasingId(packageId)
      setPurchaseError(null)
      try {
        const info = await purchaseAddon(packageId)
        onClose()
        router.push(`/chat/payment/${info.paymentId}`)
      } catch (err) {
        setPurchaseError(
          (err as Error).message || 'Không thể khởi tạo thanh toán'
        )
      } finally {
        setPurchasingId(null)
      }
    },
    [onClose, router]
  )

  const handleGoUpgrade = () => {
    onClose()
    router.push('/chat/upgrade')
  }

  const handleClose = () => {
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
      </DialogContent>
    </Dialog>
  )
}
