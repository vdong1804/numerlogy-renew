/**
 * Payment card with Approve / Reject actions.
 * Used in /admin/payments list and detail pages.
 */
import * as React from 'react'
import { Check, CreditCard, X } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'
import { Separator } from '@/components/ui/separator'
import { patchJson } from '@/lib/admin-api'
import { formatDateTimeVi, formatVnd } from '@/lib/utils'

import ConfirmDialog from './confirm-dialog'
import { toast } from './admin-toast'

export interface Payment {
  id: number
  status: number
  amount: number
  created_at: string
  user?: { id: number; email: string; full_name?: string }
  package?: { id: number; name: string }
}

const STATUS_MAP: Record<number, { label: string; variant: 'warning' | 'success' | 'destructive' }> = {
  1: { label: 'Chờ duyệt', variant: 'warning' },
  2: { label: 'Đã duyệt', variant: 'success' },
  3: { label: 'Từ chối', variant: 'destructive' },
}

interface PaymentApprovalCardProps {
  payment: Payment
  onStatusChange?: (updated: Payment) => void
}

export default function PaymentApprovalCard({ payment, onStatusChange }: PaymentApprovalCardProps) {
  const [dialog, setDialog] = React.useState<'approve' | 'reject' | null>(null)
  const [loading, setLoading] = React.useState(false)
  const [currentStatus, setCurrentStatus] = React.useState(payment.status)

  const handleAction = async (status: 2 | 3) => {
    setLoading(true)
    try {
      const updated = await patchJson<Payment>(`/admin/payments/${payment.id}/status`, { status })
      setCurrentStatus(status)
      onStatusChange?.(updated)
      toast.success(status === 2 ? 'Đã duyệt thanh toán' : 'Đã từ chối thanh toán')
    } catch (err) {
      toast.error((err as Error).message)
    } finally {
      setLoading(false)
      setDialog(null)
    }
  }

  const badge = STATUS_MAP[currentStatus] ?? { label: String(currentStatus), variant: 'warning' as const }

  return (
    <Card className="admin-card-hover overflow-hidden">
      <CardContent className="p-5">
        <div className="flex items-start gap-3">
          <span className="flex items-center justify-center w-10 h-10 rounded-lg bg-primary/10 text-primary shrink-0">
            <CreditCard className="w-5 h-5" />
          </span>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-sm font-semibold">#{payment.id}</span>
              <Badge variant={badge.variant}>{badge.label}</Badge>
              <span className="text-xs text-muted-foreground">{formatDateTimeVi(payment.created_at)}</span>
            </div>
            <p className="mt-1 text-lg font-bold tracking-tight">{formatVnd(payment.amount)}</p>
          </div>
        </div>

        <Separator className="my-4" />

        <dl className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-2 text-sm">
          {payment.user && (
            <Field label="Người dùng">
              <div className="flex flex-col min-w-0">
                <span className="truncate font-medium">
                  {payment.user.full_name || payment.user.email}
                </span>
                <span className="text-xs text-muted-foreground truncate">{payment.user.email}</span>
              </div>
            </Field>
          )}
          {payment.package && (
            <Field label="Gói">
              <span className="truncate">{payment.package.name}</span>
            </Field>
          )}
        </dl>

        {currentStatus === 1 && (
          <div className="flex items-center gap-2 mt-5">
            <Button variant="success" disabled={loading} onClick={() => setDialog('approve')}>
              <Check className="w-4 h-4" /> Duyệt
            </Button>
            <Button variant="destructive" disabled={loading} onClick={() => setDialog('reject')}>
              <X className="w-4 h-4" /> Từ chối
            </Button>
          </div>
        )}
      </CardContent>

      <ConfirmDialog
        open={dialog === 'approve'}
        title="Duyệt thanh toán"
        message={`Xác nhận duyệt thanh toán #${payment.id} với số tiền ${formatVnd(payment.amount)}?`}
        confirmLabel="Duyệt"
        loading={loading}
        onConfirm={() => handleAction(2)}
        onCancel={() => setDialog(null)}
      />
      <ConfirmDialog
        open={dialog === 'reject'}
        title="Từ chối thanh toán"
        message={`Xác nhận từ chối thanh toán #${payment.id}? Người dùng sẽ không nhận được quota.`}
        confirmLabel="Từ chối"
        danger
        loading={loading}
        onConfirm={() => handleAction(3)}
        onCancel={() => setDialog(null)}
      />
    </Card>
  )
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex items-baseline gap-2 min-w-0">
      <dt className="text-xs text-muted-foreground shrink-0 w-24">{label}</dt>
      <dd className="text-sm min-w-0 flex-1">{children}</dd>
    </div>
  )
}
