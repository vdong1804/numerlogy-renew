/**
 * Prompt editor — edit the chatbot system prompt with version banner + history.
 *
 * Backend: GET / PUT / DELETE /admin/chatbot/prompt + GET /admin/chatbot/prompt/history.
 * "Override" means a DB row exists; "default" means the in-code constant is in use.
 */
import { useEffect, useState } from 'react'
import { Loader2, RotateCcw, Save } from 'lucide-react'

import { toast } from '@/components/admin/admin-toast'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { Textarea } from '@/components/ui/textarea'
import { del, getJson, putJson } from '@/lib/admin-api'
import { formatDateVi } from '@/lib/utils'

import type {
  PromptHistoryEntry,
  PromptHistoryResponse,
  PromptOut,
} from './chatbot-types'

const HISTORY_LIMIT = 20

export default function PromptEditor() {
  const [current, setCurrent] = useState<PromptOut | null>(null)
  const [draft, setDraft] = useState('')
  const [history, setHistory] = useState<PromptHistoryEntry[]>([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [resetting, setResetting] = useState(false)
  const [error, setError] = useState('')

  async function load() {
    setLoading(true)
    setError('')
    try {
      const [prompt, hist] = await Promise.all([
        getJson<PromptOut>('/admin/chatbot/prompt'),
        getJson<PromptHistoryResponse>(
          `/admin/chatbot/prompt/history?limit=${HISTORY_LIMIT}`
        ),
      ])
      setCurrent(prompt)
      setDraft(prompt.value)
      setHistory(hist.items)
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  async function save() {
    if (!draft.trim()) {
      toast.error('Prompt không được để trống')
      return
    }
    setSaving(true)
    try {
      const next = await putJson<PromptOut>('/admin/chatbot/prompt', {
        value: draft,
      })
      setCurrent(next)
      toast.success(`Đã lưu (version ${next.version})`)
      await load()
    } catch (err) {
      toast.error((err as Error).message)
    } finally {
      setSaving(false)
    }
  }

  async function resetToDefault() {
    if (!confirm('Xóa override và quay về prompt mặc định?')) return
    setResetting(true)
    try {
      await del('/admin/chatbot/prompt')
      toast.success('Đã reset về prompt mặc định')
      await load()
    } catch (err) {
      toast.error((err as Error).message)
    } finally {
      setResetting(false)
    }
  }

  const dirty = current !== null && draft !== current.value
  const charCount = draft.length

  return (
    <div className="space-y-6">
      {error && (
        <div className="rounded-md border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive">
          {error}
        </div>
      )}

      <Card>
        <CardHeader className="flex flex-row items-center justify-between gap-4 space-y-0">
          <div>
            <CardTitle className="text-base">System Prompt</CardTitle>
            <CardDescription>
              {loading ? (
                <Skeleton className="h-4 w-40 mt-1" />
              ) : current?.is_override ? (
                <span className="inline-flex items-center gap-2">
                  <Badge>Override v{current.version}</Badge>
                  <span className="text-xs text-muted-foreground">
                    cập nhật {current.updated_at ? formatDateVi(current.updated_at) : '—'}
                  </span>
                </span>
              ) : (
                <Badge variant="secondary">Default (in-code)</Badge>
              )}
            </CardDescription>
          </div>
          <div className="flex items-center gap-2">
            {current?.is_override && (
              <Button
                variant="outline"
                size="sm"
                onClick={resetToDefault}
                disabled={resetting || saving}
              >
                {resetting ? (
                  <Loader2 className="w-4 h-4 mr-1 animate-spin" />
                ) : (
                  <RotateCcw className="w-4 h-4 mr-1" />
                )}
                Reset
              </Button>
            )}
            <Button onClick={save} disabled={!dirty || saving || loading}>
              {saving ? (
                <Loader2 className="w-4 h-4 mr-1 animate-spin" />
              ) : (
                <Save className="w-4 h-4 mr-1" />
              )}
              Lưu
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {loading ? (
            <Skeleton className="h-72 w-full" />
          ) : (
            <Textarea
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              rows={16}
              className="font-mono text-xs"
              maxLength={20000}
              placeholder="Nội dung system prompt..."
            />
          )}
          <p className="mt-2 text-xs text-muted-foreground tabular-nums">
            {charCount.toLocaleString()} ký tự {dirty && '· chưa lưu'}
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Lịch sử thay đổi</CardTitle>
          <CardDescription>{history.length} bản gần nhất</CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <Skeleton className="h-24 w-full" />
          ) : history.length === 0 ? (
            <p className="text-sm text-muted-foreground">Chưa có thay đổi nào.</p>
          ) : (
            <ul className="space-y-2">
              {history.map((h) => (
                <li
                  key={h.id}
                  className="rounded-md border border-border/70 p-3 hover:bg-accent/30"
                >
                  <div className="flex items-center justify-between gap-3">
                    <div className="flex items-center gap-2">
                      <Badge variant="outline">v{h.version}</Badge>
                      <span className="text-xs text-muted-foreground">
                        {formatDateVi(h.changed_at)} · by user #{h.changed_by ?? '—'}
                      </span>
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setDraft(h.value)}
                    >
                      Load vào editor
                    </Button>
                  </div>
                  <p className="mt-2 text-xs font-mono text-muted-foreground line-clamp-3 whitespace-pre-wrap">
                    {h.value}
                  </p>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
