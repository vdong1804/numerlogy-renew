/**
 * PdfUploadButton — triggers file picker for PDF, shows attached filename + remove.
 * Delegates actual upload to usePdfUpload hook passed via props.
 * Disabled with explanatory tooltip when no conversation is selected.
 */

import { Loader2, Paperclip, X } from 'lucide-react'
import { useRef, useState } from 'react'

import { cn } from '@/lib/utils'

interface PdfUploadButtonProps {
  filename: string | null
  uploading: boolean
  error: string | null
  onFileSelect: (file: File) => void
  /** Async — awaits server PATCH to clear pdf context */
  onRemove: () => Promise<void>
  disabled?: boolean
  /** When false, upload is blocked: no active conversation to attach PDF to */
  hasConversation?: boolean
}

export default function PdfUploadButton({
  filename,
  uploading,
  error,
  onFileSelect,
  onRemove,
  disabled = false,
  hasConversation = true,
}: PdfUploadButtonProps) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [removing, setRemoving] = useState(false)

  const isDisabled = disabled || uploading || !hasConversation || removing

  const handleClick = () => {
    if (isDisabled) return
    inputRef.current?.click()
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) onFileSelect(file)
    // Reset so same file can be re-selected
    e.target.value = ''
  }

  const handleRemove = async () => {
    setRemoving(true)
    try {
      await onRemove()
    } finally {
      setRemoving(false)
    }
  }

  // Attached state — show pill with filename + remove button
  if (filename) {
    return (
      <div className="flex items-center gap-1.5 rounded-full bg-primary/10 border border-primary/20 px-2.5 py-1 text-xs max-w-[160px]">
        <Paperclip className="w-3 h-3 text-primary shrink-0" />
        <span className="truncate text-primary font-medium" title={filename}>
          {filename}
        </span>
        <button
          type="button"
          aria-label="Gỡ file PDF"
          onClick={handleRemove}
          disabled={isDisabled}
          className="ml-0.5 shrink-0 rounded-full p-0.5 text-primary/70 hover:text-primary hover:bg-primary/20 transition-colors"
        >
          {removing ? (
            <Loader2 className="w-3 h-3 animate-spin" />
          ) : (
            <X className="w-3 h-3" />
          )}
        </button>
      </div>
    )
  }

  const buttonTitle = !hasConversation
    ? 'Vui lòng chọn hoặc tạo cuộc trò chuyện trước'
    : error ?? 'Đính kèm PDF'

  return (
    <>
      <input
        ref={inputRef}
        type="file"
        accept="application/pdf"
        className="hidden"
        aria-hidden="true"
        onChange={handleChange}
      />
      <button
        type="button"
        aria-label="Đính kèm PDF"
        onClick={handleClick}
        disabled={isDisabled}
        title={buttonTitle}
        className={cn(
          'flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-medium border transition-colors',
          error
            ? 'border-destructive/40 text-destructive bg-destructive/5'
            : 'border-border text-muted-foreground hover:border-primary/40 hover:text-primary hover:bg-primary/5',
          isDisabled && 'opacity-50 cursor-not-allowed'
        )}
      >
        {uploading ? (
          <Loader2 className="w-3.5 h-3.5 animate-spin" />
        ) : (
          <Paperclip className="w-3.5 h-3.5" />
        )}
        {uploading ? 'Đang tải...' : 'Đính kèm PDF'}
      </button>
    </>
  )
}
