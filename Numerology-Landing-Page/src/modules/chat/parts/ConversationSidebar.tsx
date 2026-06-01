/**
 * ConversationSidebar — list conversations, new + delete with confirm dialog.
 * Items show title + relative timestamp; trash icon revealed on hover/focus.
 * Footer pins user identity + quick upgrade link for visual grounding.
 */

import {
  MessageSquare,
  MessageSquarePlus,
  Sparkles,
  Trash2,
} from 'lucide-react'
import Link from 'next/link'
import { useState } from 'react'

import ConfirmDialog from '@/components/admin/confirm-dialog'
import type { AuthUser } from '@/lib/user-auth'
import { cn, formatRelativeVi } from '@/lib/utils'
import type { Conversation } from '@/models/Chat'

interface ConversationSidebarProps {
  conversations: Conversation[]
  activeId: number | null
  loading: boolean
  user: AuthUser | null
  onSelect: (id: number) => void
  onCreate: () => void
  onDelete: (id: number) => void
}

export default function ConversationSidebar({
  conversations,
  activeId,
  loading,
  user,
  onSelect,
  onCreate,
  onDelete,
}: ConversationSidebarProps) {
  const [confirmId, setConfirmId] = useState<number | null>(null)
  const [deleting, setDeleting] = useState(false)

  const handleDelete = async () => {
    if (confirmId == null) return
    setDeleting(true)
    try {
      onDelete(confirmId)
    } finally {
      setDeleting(false)
      setConfirmId(null)
    }
  }

  const fullName = user
    ? `${user.first_name ?? ''} ${user.last_name ?? ''}`.trim() ||
      user.email.split('@')[0]
    : ''
  const initial = (fullName || user?.email || '?').charAt(0).toUpperCase()

  return (
    <aside
      className="flex flex-col h-full"
      aria-label="Danh sách cuộc trò chuyện"
    >
      {/* New conversation */}
      <div className="px-3 pt-3 pb-2">
        <button
          type="button"
          onClick={onCreate}
          aria-label="Cuộc trò chuyện mới"
          className="w-full inline-flex items-center justify-center gap-2 rounded-xl bg-primary text-primary-foreground hover:bg-primary/90 px-3 py-2.5 text-sm font-medium transition-colors shadow-sm hover:shadow-md hover:shadow-primary/20"
        >
          <MessageSquarePlus className="w-4 h-4" aria-hidden="true" />
          Cuộc trò chuyện mới
        </button>
      </div>

      {/* Section label */}
      <div className="px-4 pt-2 pb-1">
        <p className="text-[11px] uppercase tracking-wider font-semibold text-muted-foreground/80">
          Gần đây
        </p>
      </div>

      {/* List */}
      <nav className="flex-1 overflow-y-auto px-2 pb-2 space-y-0.5">
        {loading && (
          <div className="space-y-1.5 px-1 pt-1">
            {[1, 2, 3, 4].map((n) => (
              <div
                key={n}
                className="h-12 rounded-lg bg-muted/60 animate-pulse"
              />
            ))}
          </div>
        )}

        {!loading && conversations.length === 0 && (
          <div className="flex flex-col items-center text-center px-3 py-10">
            <MessageSquare
              className="w-8 h-8 text-muted-foreground/40 mb-2"
              aria-hidden="true"
            />
            <p className="text-xs text-muted-foreground">
              Chưa có cuộc trò chuyện nào.
            </p>
            <p className="text-[11px] text-muted-foreground/70 mt-1">
              Nhấn nút phía trên để bắt đầu.
            </p>
          </div>
        )}

        {conversations.map((conv) => {
          const isActive = activeId === conv.id
          return (
            <div
              key={conv.id}
              className={cn(
                'group relative flex items-center gap-2 rounded-lg px-2.5 py-2 text-sm cursor-pointer transition-colors',
                isActive
                  ? 'bg-primary/10 text-foreground'
                  : 'text-foreground/80 hover:bg-muted/60'
              )}
              role="button"
              tabIndex={0}
              aria-current={isActive ? 'page' : undefined}
              onClick={() => onSelect(conv.id)}
              onKeyDown={(e) => e.key === 'Enter' && onSelect(conv.id)}
            >
              {isActive && (
                <span
                  aria-hidden="true"
                  className="absolute left-0 top-1/2 -translate-y-1/2 h-6 w-0.5 rounded-r bg-primary"
                />
              )}
              <MessageSquare
                className={cn(
                  'w-4 h-4 shrink-0',
                  isActive ? 'text-primary' : 'text-muted-foreground'
                )}
                aria-hidden="true"
              />
              <div className="flex-1 min-w-0">
                <p
                  className={cn(
                    'truncate leading-tight',
                    isActive ? 'font-semibold' : 'font-medium'
                  )}
                >
                  {conv.title}
                </p>
                <p className="text-[11px] text-muted-foreground truncate mt-0.5">
                  {formatRelativeVi(conv.createdAt)}
                </p>
              </div>
              <button
                type="button"
                aria-label={`Xóa: ${conv.title}`}
                onClick={(e) => {
                  e.stopPropagation()
                  setConfirmId(conv.id)
                }}
                className="shrink-0 opacity-0 group-hover:opacity-100 focus:opacity-100 rounded p-1 text-muted-foreground hover:text-destructive hover:bg-destructive/10 transition-all"
              >
                <Trash2 className="w-3.5 h-3.5" />
              </button>
            </div>
          )
        })}
      </nav>

      {/* Footer — upgrade banner + user mini-card */}
      <div className="border-t border-border p-3 space-y-2">
        <Link
          href="/chat/upgrade"
          className="flex items-center gap-2 rounded-lg border border-primary/30 bg-primary/5 hover:bg-primary/10 px-3 py-2 text-xs transition-colors"
        >
          <Sparkles
            className="w-3.5 h-3.5 text-primary shrink-0"
            aria-hidden="true"
          />
          <span className="flex-1 truncate font-medium text-foreground">
            Nâng cấp gói chat
          </span>
        </Link>

        {user && (
          <Link
            href="/my-account"
            className="flex items-center gap-2 rounded-lg px-2 py-1.5 hover:bg-muted/60 transition-colors"
          >
            <span className="shrink-0 inline-flex items-center justify-center w-8 h-8 rounded-full bg-primary/20 text-primary text-xs font-bold">
              {initial}
            </span>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-medium text-foreground truncate">
                {fullName}
              </p>
              <p className="text-[11px] text-muted-foreground truncate">
                {user.email}
              </p>
            </div>
          </Link>
        )}
      </div>

      {/* Delete confirm */}
      <ConfirmDialog
        open={confirmId != null}
        title="Xóa cuộc trò chuyện?"
        message="Hành động này không thể hoàn tác. Toàn bộ tin nhắn sẽ bị xóa."
        confirmLabel="Xóa"
        cancelLabel="Hủy"
        danger
        loading={deleting}
        onConfirm={handleDelete}
        onCancel={() => setConfirmId(null)}
      />
    </aside>
  )
}
