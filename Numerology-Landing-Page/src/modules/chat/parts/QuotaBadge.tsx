/**
 * QuotaBadge — displays current quota state in the chat header.
 * - addon source: "<n> Pro" or "<n> Flash" + expiry tooltip
 * - free source: "<used>/<limit>" + daily limit tooltip
 * - canSend=false: red "Hết lượt" badge → triggers onExhausted callback
 * Click → navigate to /chat/upgrade (except when exhausted → opens upsell modal).
 */

import { MessageCircle, Zap } from 'lucide-react'
import { useRouter } from 'next/router'

import { cn, formatDateVi } from '@/lib/utils'
import type { Quota } from '@/models/Chat'

interface QuotaBadgeProps {
  quota: Quota
  onExhausted: () => void
}

export default function QuotaBadge({ quota, onExhausted }: QuotaBadgeProps) {
  const router = useRouter()

  const handleClick = () => {
    if (!quota.canSend) {
      onExhausted()
      return
    }
    router.push('/chat/upgrade')
  }

  // Determine display label + tooltip
  let label: string
  let tooltip: string
  let colorClass: string

  if (!quota.canSend) {
    label = 'Hết lượt'
    tooltip = 'Bạn đã hết lượt nhắn tin. Nhấn để nâng cấp.'
    colorClass =
      'bg-destructive/10 text-destructive border-destructive/30 hover:bg-destructive/20'
  } else if (quota.decisionSource === 'addon') {
    const tierLabel = quota.addonTier === 'pro' ? 'Pro' : 'Flash'
    label = `${quota.addonRemaining} ${tierLabel}`
    tooltip = quota.addonExpiresAt
      ? `Hết hạn ${formatDateVi(quota.addonExpiresAt)}`
      : 'Gói tin nhắn đang hoạt động'
    colorClass =
      'bg-primary/10 text-primary border-primary/30 hover:bg-primary/20'
  } else {
    // free source or null
    label = `${quota.freeUsedToday}/${quota.freeLimit}`
    tooltip = 'Hạn mức miễn phí hôm nay'
    colorClass =
      'bg-muted text-muted-foreground border-border hover:bg-muted/80'
  }

  const Icon = quota.decisionSource === 'addon' ? Zap : MessageCircle

  return (
    <button
      type="button"
      onClick={handleClick}
      title={tooltip}
      aria-label={`Hạn mức chat: ${label}. ${tooltip}`}
      className={cn(
        'inline-flex items-center gap-1 px-2 py-0.5 rounded-full border text-xs font-medium',
        'transition-colors cursor-pointer select-none shrink-0',
        colorClass
      )}
    >
      <Icon className="w-3 h-3" aria-hidden="true" />
      <span>{label}</span>
    </button>
  )
}
