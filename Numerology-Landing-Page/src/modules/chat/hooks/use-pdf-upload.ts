/**
 * usePdfUpload — multipart upload to POST /api/chat/conversations/{id}/upload-pdf
 * Requires a conversationId (conversation must exist before upload).
 * Exposes { pdfContextId, filename } where filename is the local File.name.
 */

import { useCallback, useState } from 'react'

import { clearPdfContext, uploadPdf } from '../api/chat-api'

const MAX_FILE_SIZE_MB = 20

interface PdfAttachment {
  pdfContextId: number
  /** Local filename from File.name — not from server response */
  filename: string
}

interface UsePdfUploadReturn {
  attachment: PdfAttachment | null
  uploading: boolean
  error: string | null
  upload: (file: File) => Promise<void>
  /** Async — calls PATCH to clear server attachment when conversationId is set */
  clear: () => Promise<void>
}

/**
 * @param conversationId - Active conversation id. Pass null when no conversation
 *   is selected; upload() will be a no-op and the button should be disabled.
 */
export function usePdfUpload(
  conversationId: number | null
): UsePdfUploadReturn {
  const [attachment, setAttachment] = useState<PdfAttachment | null>(null)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const upload = useCallback(
    async (file: File) => {
      if (conversationId == null) {
        setError('Vui lòng chọn hoặc tạo cuộc trò chuyện trước.')
        return
      }
      setError(null)

      // Client-side size guard (server enforces hard limit too)
      if (file.size > MAX_FILE_SIZE_MB * 1024 * 1024) {
        setError(`File quá lớn. Tối đa ${MAX_FILE_SIZE_MB}MB.`)
        return
      }
      if (file.type !== 'application/pdf') {
        setError('Chỉ chấp nhận file PDF.')
        return
      }

      setUploading(true)
      try {
        const result = await uploadPdf(conversationId, file)
        setAttachment({
          pdfContextId: result.pdfContextId,
          // filename comes from local File object, not server response
          filename: file.name,
        })
      } catch (err) {
        setError((err as Error).message || 'Tải PDF thất bại')
      } finally {
        setUploading(false)
      }
    },
    [conversationId]
  )

  const clear = useCallback(async () => {
    if (conversationId == null) {
      // No conversation — local-only clear
      setAttachment(null)
      setError(null)
      return
    }
    // Optimistic: clear local state immediately
    const previous = attachment
    setAttachment(null)
    setError(null)
    try {
      await clearPdfContext(conversationId)
    } catch (err) {
      // Revert on failure and surface error
      setAttachment(previous)
      setError((err as Error).message || 'Xóa PDF thất bại')
    }
  }, [conversationId, attachment])

  return { attachment, uploading, error, upload, clear }
}
