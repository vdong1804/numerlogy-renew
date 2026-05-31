/**
 * QRDisplay — placeholder QR for Phase 1 (real VietQR generated in Phase 2).
 *
 * Renders a static rounded box with the bank info + an amount/ref overlay.
 * Phase 2 will swap the inner <img> for a server-rendered VietQR URL.
 */
import { formatVnd } from '@/lib/utils'

interface Props {
  amount: number
  refCode: string
  /** Optional — populated in phase 2 once SePay/bank config is in place. */
  qrUrl?: string
  bankName?: string
  accountNumber?: string
  accountHolder?: string
}

export default function QrDisplay({
  amount,
  refCode,
  qrUrl,
  bankName,
  accountNumber,
  accountHolder,
}: Props) {
  return (
    <div className="rounded-xl border border-border bg-card p-5 flex flex-col items-center text-center">
      <div className="w-64 h-64 rounded-lg border-2 border-dashed border-border flex items-center justify-center bg-muted/50">
        {qrUrl ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={qrUrl} alt={`QR ${refCode}`} className="w-full h-full object-contain" />
        ) : (
          <span className="text-sm text-muted-foreground px-3">
            QR sẽ xuất hiện sau khi tích hợp SePay (Phase 2)
          </span>
        )}
      </div>
      <div className="mt-4 text-sm space-y-1 w-full max-w-xs">
        <div className="flex justify-between">
          <span className="text-muted-foreground">Số tiền</span>
          <span className="font-semibold">{formatVnd(amount)}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-muted-foreground">Mã giao dịch</span>
          <span className="font-mono font-semibold">{refCode}</span>
        </div>
        {bankName && (
          <div className="flex justify-between">
            <span className="text-muted-foreground">Ngân hàng</span>
            <span>{bankName}</span>
          </div>
        )}
        {accountNumber && (
          <div className="flex justify-between">
            <span className="text-muted-foreground">Số TK</span>
            <span className="font-mono">{accountNumber}</span>
          </div>
        )}
        {accountHolder && (
          <div className="flex justify-between">
            <span className="text-muted-foreground">Chủ TK</span>
            <span>{accountHolder}</span>
          </div>
        )}
      </div>
    </div>
  )
}
