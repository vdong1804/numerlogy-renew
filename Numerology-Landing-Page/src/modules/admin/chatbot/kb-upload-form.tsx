/**
 * Drag-drop / picker form for admin KB uploads.
 * Accepts PDF, DOCX, TXT, MD. Posts multipart to /admin/chatbot/kb/upload.
 */
import { useRef, useState } from 'react'
import { FileText, Loader2, Upload } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent } from '@/components/ui/card'
import { toast } from '@/components/admin/admin-toast'
import { cn } from '@/lib/utils'

import type { KbUploadResponse } from './chatbot-types'

const ACCEPT = '.pdf,.docx,.txt,.md'
const MAX_BYTES = 100 * 1024 * 1024
const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? 'http://localhost:8000'
const TOKEN_KEY = 'admin_access_token'

interface Props {
  onUploaded: (resp: KbUploadResponse) => void
}

export default function KbUploadForm({ onUploaded }: Props) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [file, setFile] = useState<File | null>(null)
  const [title, setTitle] = useState('')
  const [busy, setBusy] = useState(false)
  const [dragging, setDragging] = useState(false)

  function pickFile(f: File | null) {
    if (!f) {
      setFile(null)
      return
    }
    if (f.size > MAX_BYTES) {
      toast.error('File quá lớn (tối đa 100 MB)')
      return
    }
    setFile(f)
    if (!title) setTitle(f.name)
  }

  async function handleUpload() {
    if (!file) {
      toast.error('Chọn file trước khi upload')
      return
    }
    setBusy(true)
    try {
      const form = new FormData()
      form.append('file', file)
      const qs = title ? `?title=${encodeURIComponent(title)}` : ''
      const token = typeof window !== 'undefined' ? localStorage.getItem(TOKEN_KEY) : null
      const res = await fetch(`${API_BASE}/admin/chatbot/kb/upload${qs}`, {
        method: 'POST',
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        body: form,
      })
      if (!res.ok) {
        const msg = await res.text().catch(() => res.statusText)
        throw new Error(msg)
      }
      const data = (await res.json()) as KbUploadResponse
      toast.success(`Đã ingest ${data.chunks_created} chunk từ "${data.document.title}"`)
      onUploaded(data)
      setFile(null)
      setTitle('')
      if (inputRef.current) inputRef.current.value = ''
    } catch (err) {
      toast.error((err as Error).message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <Card>
      <CardContent className="p-5 space-y-4">
        <div
          className={cn(
            'border-2 border-dashed rounded-lg px-4 py-8 text-center transition-colors',
            dragging
              ? 'border-primary bg-primary/5'
              : 'border-border hover:border-primary/50'
          )}
          onDragEnter={(e) => {
            e.preventDefault()
            setDragging(true)
          }}
          onDragLeave={() => setDragging(false)}
          onDragOver={(e) => e.preventDefault()}
          onDrop={(e) => {
            e.preventDefault()
            setDragging(false)
            pickFile(e.dataTransfer.files?.[0] ?? null)
          }}
        >
          <input
            ref={inputRef}
            type="file"
            accept={ACCEPT}
            hidden
            onChange={(e) => pickFile(e.target.files?.[0] ?? null)}
          />
          {file ? (
            <div className="flex items-center justify-center gap-2 text-sm">
              <FileText className="w-4 h-4 text-primary" />
              <span className="font-medium">{file.name}</span>
              <span className="text-xs text-muted-foreground">
                ({(file.size / 1024).toFixed(0)} KB)
              </span>
            </div>
          ) : (
            <div className="flex flex-col items-center gap-2">
              <Upload className="w-7 h-7 text-muted-foreground" />
              <p className="text-sm text-muted-foreground">
                Kéo & thả PDF / DOCX / TXT vào đây
              </p>
              <p className="text-xs text-muted-foreground">Tối đa 100 MB</p>
            </div>
          )}
          <Button
            type="button"
            variant="outline"
            size="sm"
            className="mt-3"
            onClick={() => inputRef.current?.click()}
          >
            Chọn file
          </Button>
        </div>

        <div className="space-y-2">
          <label htmlFor="kb-title" className="text-xs font-medium text-muted-foreground">
            Tiêu đề (tùy chọn)
          </label>
          <Input
            id="kb-title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Ví dụ: Hướng dẫn tra cứu thần số học 2026"
            maxLength={500}
          />
        </div>

        <div className="flex justify-end gap-2">
          <Button
            variant="ghost"
            disabled={!file || busy}
            onClick={() => {
              setFile(null)
              setTitle('')
              if (inputRef.current) inputRef.current.value = ''
            }}
          >
            Hủy
          </Button>
          <Button onClick={handleUpload} disabled={!file || busy}>
            {busy ? <Loader2 className="w-4 h-4 animate-spin mr-1" /> : <Upload className="w-4 h-4 mr-1" />}
            {busy ? 'Đang upload...' : 'Upload + Ingest'}
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}
