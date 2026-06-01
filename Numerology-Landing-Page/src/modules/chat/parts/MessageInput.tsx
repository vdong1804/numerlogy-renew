/**
 * MessageInput — auto-expanding textarea (max 8 rows), Enter to send,
 * Shift+Enter for newline. PDF attach + send button live inside the input
 * container for a unified, modern chat composer.
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
    <div className="border-t border-border bg-background px-3 py-3 sticky bottom-0 pb-[max(env(safe-area-inset-bottom,12px),12px)]">
      <div className="max-w-3xl mx-auto">
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
          <p
            className="mb-1.5 text-xs text-warning/80 text-center"
            role="status"
          >
            Chờ {rateLimitSecondsLeft}s trước khi gửi tin nhắn mới
          </p>
        )}

        {/* Unified input container */}
        <div
          className={cn(
            'flex flex-col rounded-2xl border border-input bg-card shadow-sm transition-all',
            'focus-within:border-primary/60 focus-within:ring-2 focus-within:ring-primary/20'
          )}
        >
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
              'w-full resize-none bg-transparent px-4 pt-3 pb-1 text-sm leading-6 text-foreground caret-primary',
              'placeholder:text-muted-foreground focus-visible:outline-none',
              'disabled:cursor-not-allowed disabled:opacity-50'
            )}
          />

          <div className="flex items-center gap-2 px-2 pb-2">
            <PdfUploadButton
              filename={pdfFilename}
              uploading={pdfUploading}
              error={pdfError}
              onFileSelect={onPdfSelect}
              onRemove={onPdfRemove}
              disabled={disabled || isStreaming}
            />

            <div className="flex-1" />

            {isStreaming ? (
              <button
                type="button"
                onClick={onCancel}
                aria-label="Dừng phản hồi"
                className="shrink-0 inline-flex items-center justify-center w-9 h-9 rounded-full bg-destructive/10 text-destructive hover:bg-destructive/20 transition-colors border border-destructive/20"
              >
                <Square className="w-4 h-4" fill="currentColor" />
              </button>
            ) : (
              <button
                type="button"
                onClick={onSend}
                disabled={!canSend}
                aria-label="Gửi tin nhắn"
                className={cn(
                  'shrink-0 inline-flex items-center justify-center w-9 h-9 rounded-full transition-all',
                  canSend
                    ? 'bg-primary text-primary-foreground hover:bg-primary/90 shadow-sm hover:shadow'
                    : 'bg-muted text-muted-foreground cursor-not-allowed'
                )}
              >
                <Send className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>

        {/* Footnote */}
        <p className="mt-1.5 text-[11px] text-muted-foreground/70 text-center">
          {isStreaming
            ? 'Đang trả lời...'
            : 'AI có thể mắc lỗi — vui lòng kiểm chứng thông tin quan trọng.'}
        </p>
      </div>
    </div>
  )
}
