/**
 * MessageInput — auto-expanding textarea (max 8 rows), Enter to send,
 * Shift+Enter for newline, send button + PDF attach. Disabled while streaming.
 * Sticky bottom on mobile via CSS class in chat.module.css.
 */

import { Send, Square } from 'lucide-react'
import { useCallback, useEffect, useRef } from 'react'

import { cn } from '@/lib/utils'

import PdfUploadButton from './PdfUploadButton'

interface MessageInputProps {
  value: string
  onChange: (val: string) => void
  onSend: () => void
  onCancel: () => void
  isStreaming: boolean
  disabled: boolean
  /** PDF attachment state threaded from parent */
  pdfFilename: string | null
  pdfUploading: boolean
  pdfError: string | null
  onPdfSelect: (file: File) => void
  /** Async — awaits server PATCH to clear pdf context */
  onPdfRemove: () => Promise<void>
  /** Quota-based send gate — false shows hint and disables send */
  quotaCanSend?: boolean
  /** Rate-limit countdown active — disables send and shows wait hint */
  rateLimitActive?: boolean
  /** Seconds remaining in rate-limit cooldown */
  rateLimitSecondsLeft?: number
}

const MAX_ROWS = 8
const LINE_HEIGHT_PX = 24

export default function MessageInput({
  value,
  onChange,
  onSend,
  onCancel,
  isStreaming,
  disabled,
  pdfFilename,
  pdfUploading,
  pdfError,
  onPdfSelect,
  onPdfRemove,
  quotaCanSend = true,
  rateLimitActive = false,
  rateLimitSecondsLeft = 0,
}: MessageInputProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  // Auto-expand textarea height
  const resize = useCallback(() => {
    const el = textareaRef.current
    if (!el) return
    el.style.height = 'auto'
    const maxHeight = MAX_ROWS * LINE_HEIGHT_PX
    el.style.height = `${Math.min(el.scrollHeight, maxHeight)}px`
    el.style.overflowY = el.scrollHeight > maxHeight ? 'auto' : 'hidden'
  }, [])

  useEffect(() => {
    resize()
  }, [value, resize])

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      if (!disabled && !isStreaming && !rateLimitActive && value.trim())
        onSend()
    }
  }

  const canSend =
    !disabled &&
    !isStreaming &&
    value.trim().length > 0 &&
    quotaCanSend &&
    !rateLimitActive

  return (
    <div className="border-t border-border bg-background px-3 py-3 sticky bottom-0 pb-[env(safe-area-inset-bottom,12px)]">
      {/* PDF attachment row */}
      <div className="flex items-center gap-2 mb-2">
        <PdfUploadButton
          filename={pdfFilename}
          uploading={pdfUploading}
          error={pdfError}
          onFileSelect={onPdfSelect}
          onRemove={onPdfRemove}
          disabled={disabled || isStreaming}
        />
      </div>

      {/* Quota exhausted hint */}
      {!quotaCanSend && !isStreaming && (
        <p
          className="mb-1.5 text-xs text-destructive/80 text-center"
          role="status"
        >
          Đã hết lượt miễn phí — mua thêm gói để tiếp tục
        </p>
      )}

      {/* Rate-limit countdown hint */}
      {rateLimitActive && !isStreaming && (
        <p className="mb-1.5 text-xs text-warning/80 text-center" role="status">
          Chờ {rateLimitSecondsLeft}s trước khi gửi tin nhắn mới
        </p>
      )}

      {/* Input row */}
      <div className="flex items-end gap-2">
        <textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={disabled || isStreaming}
          placeholder="Nhập câu hỏi... (Enter để gửi, Shift+Enter xuống dòng)"
          aria-label="Nhập tin nhắn"
          rows={1}
          className={cn(
            'flex-1 resize-none rounded-xl border border-input bg-background px-3 py-2 text-sm shadow-sm',
            'placeholder:text-muted-foreground transition-colors leading-6',
            'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-1',
            'disabled:cursor-not-allowed disabled:opacity-50'
          )}
        />

        {isStreaming ? (
          <button
            type="button"
            onClick={onCancel}
            aria-label="Dừng phản hồi"
            className="shrink-0 flex items-center justify-center w-9 h-9 rounded-xl bg-destructive/10 text-destructive hover:bg-destructive/20 transition-colors border border-destructive/20"
          >
            <Square className="w-4 h-4" />
          </button>
        ) : (
          <button
            type="button"
            onClick={onSend}
            disabled={!canSend}
            aria-label="Gửi tin nhắn"
            className={cn(
              'shrink-0 flex items-center justify-center w-9 h-9 rounded-xl transition-colors',
              canSend
                ? 'bg-primary text-primary-foreground hover:bg-primary/90 shadow-sm'
                : 'bg-muted text-muted-foreground cursor-not-allowed'
            )}
          >
            <Send className="w-4 h-4" />
          </button>
        )}
      </div>

      {isStreaming && (
        <p className="mt-1.5 text-xs text-muted-foreground text-center animate-pulse">
          Đang trả lời...
        </p>
      )}
    </div>
  )
}
