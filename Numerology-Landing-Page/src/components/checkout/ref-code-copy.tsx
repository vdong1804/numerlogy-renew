/**
 * RefCodeCopy — large clickable ref_code with copy-to-clipboard feedback.
 *
 * The ref_code MUST appear in the bank-transfer description verbatim, so we
 * surface a one-tap copy affordance and a 2s "Đã sao chép" confirmation.
 */
import { Check, Copy } from 'lucide-react'
import { useState } from 'react'

import { Button } from '@/components/ui/button'

interface Props {
  refCode: string
}

export default function RefCodeCopy({ refCode }: Props) {
  const [copied, setCopied] = useState(false)

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(refCode)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      // Older browsers / blocked clipboard — fall back silently
    }
  }

  return (
    <div className="rounded-lg border border-primary/30 bg-primary/5 px-4 py-3 flex items-center gap-3">
      <div className="flex-1">
        <p className="text-xs text-muted-foreground">
          Nội dung chuyển khoản (bắt buộc)
        </p>
        <p className="text-xl font-mono font-bold tracking-wider text-primary">
          {refCode}
        </p>
      </div>
      <Button
        variant={copied ? 'default' : 'outline'}
        size="sm"
        onClick={handleCopy}
        aria-label="Sao chép mã giao dịch"
      >
        {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
        <span className="ml-1">{copied ? 'Đã sao chép' : 'Sao chép'}</span>
      </Button>
    </div>
  )
}
