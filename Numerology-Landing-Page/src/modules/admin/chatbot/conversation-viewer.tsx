/**
 * Modal viewer for a single conversation thread + citations.
 * Fetches GET /admin/chatbot/conversations/{id} lazily on open.
 */
import { useEffect, useState } from 'react'
import { Bot, Database, FileText, User } from 'lucide-react'

import { Badge } from '@/components/ui/badge'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Skeleton } from '@/components/ui/skeleton'
import { getJson } from '@/lib/admin-api'
import { formatDateVi } from '@/lib/utils'

import type {
  ConversationCitation,
  ConversationDetail,
  ConversationMessage,
} from './chatbot-types'

interface Props {
  conversationId: number | null
  onClose: () => void
}

export default function ConversationViewer({ conversationId, onClose }: Props) {
  const [data, setData] = useState<ConversationDetail | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (conversationId == null) {
      setData(null)
      return
    }
    let alive = true
    setLoading(true)
    setError('')
    getJson<ConversationDetail>(`/admin/chatbot/conversations/${conversationId}`)
      .then((d) => {
        if (alive) setData(d)
      })
      .catch((err) => {
        if (alive) setError((err as Error).message)
      })
      .finally(() => {
        if (alive) setLoading(false)
      })
    return () => {
      alive = false
    }
  }, [conversationId])

  return (
    <Dialog open={conversationId !== null} onOpenChange={(o) => !o && onClose()}>
      <DialogContent className="max-w-3xl max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Hội thoại #{conversationId ?? '—'}</DialogTitle>
          <DialogDescription>
            {data && (
              <span>
                User #{data.user_id} · {data.messages.length} tin nhắn · tạo{' '}
                {formatDateVi(data.created_at)}
              </span>
            )}
          </DialogDescription>
        </DialogHeader>

        {error && (
          <div className="rounded-md border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive">
            {error}
          </div>
        )}

        {loading ? (
          <div className="space-y-3">
            <Skeleton className="h-20 w-full" />
            <Skeleton className="h-32 w-full" />
            <Skeleton className="h-20 w-full" />
          </div>
        ) : data ? (
          <div className="space-y-3">
            {data.messages.map((m) => (
              <MessageBubble key={m.id} message={m} />
            ))}
          </div>
        ) : null}
      </DialogContent>
    </Dialog>
  )
}

function MessageBubble({ message }: { message: ConversationMessage }) {
  const isUser = message.role === 'user'
  const Icon = isUser ? User : Bot
  return (
    <div
      className={
        isUser
          ? 'rounded-lg border border-border/70 p-3'
          : 'rounded-lg border border-primary/30 bg-primary/5 p-3'
      }
    >
      <div className="flex items-center justify-between gap-3 mb-2">
        <div className="flex items-center gap-2 text-xs font-medium">
          <Icon className="w-3.5 h-3.5" />
          {isUser ? 'User' : 'Assistant'}
          {message.tier && <Badge variant="outline">{message.tier}</Badge>}
          {message.model_used && (
            <Badge variant="secondary" className="font-mono text-[10px]">
              {message.model_used}
            </Badge>
          )}
        </div>
        <span className="text-xs text-muted-foreground">
          {formatDateVi(message.created_at)}
        </span>
      </div>
      <p className="text-sm whitespace-pre-wrap">{message.content}</p>
      {(message.input_tokens > 0 || message.output_tokens > 0) && (
        <p className="mt-2 text-[10px] text-muted-foreground tabular-nums">
          in {message.input_tokens.toLocaleString()} · out{' '}
          {message.output_tokens.toLocaleString()} tok
        </p>
      )}
      {message.citations.length > 0 && (
        <Citations items={message.citations} />
      )}
    </div>
  )
}

function Citations({ items }: { items: ConversationCitation[] }) {
  return (
    <ul className="mt-3 space-y-1 border-t border-border/60 pt-2">
      {items.map((c, idx) => (
        <li key={idx} className="flex items-start gap-2 text-xs">
          {c.source_type === 'admin_upload' ? (
            <FileText className="w-3 h-3 mt-0.5 text-muted-foreground" />
          ) : (
            <Database className="w-3 h-3 mt-0.5 text-muted-foreground" />
          )}
          <span className="font-mono text-[10px] text-muted-foreground">
            [{c.index ?? idx + 1}]
          </span>
          <span className="flex-1">
            {c.title ?? '—'}{' '}
            <span className="text-muted-foreground">
              ({c.source_type}/{c.source_ref})
            </span>
          </span>
          {typeof c.score === 'number' && (
            <span className="font-mono text-[10px] text-muted-foreground tabular-nums">
              {c.score.toFixed(3)}
            </span>
          )}
        </li>
      ))}
    </ul>
  )
}
