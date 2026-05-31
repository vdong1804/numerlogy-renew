/**
 * ConversationSidebar — list conversations, new + delete with confirm dialog.
 */

import { MessageSquarePlus, Trash2 } from 'lucide-react'
import { useState } from 'react'

import ConfirmDialog from '@/components/admin/confirm-dialog'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import type { Conversation } from '@/models/Chat'

interface ConversationSidebarProps {
  conversations: Conversation[]
  activeId: number | null
  loading: boolean
  onSelect: (id: number) => void
  onCreate: () => void
  onDelete: (id: number) => void
}

export default function ConversationSidebar({
  conversations,
  activeId,
  loading,
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

  return (
    <aside
      className="flex flex-col h-full bg-card border-r border-border"
      aria-label="Danh sách cuộc trò chuyện"
    >
      {/* New conversation button */}
      <div className="p-3 border-b border-border">
        <Button
          onClick={onCreate}
          className="w-full gap-2 justify-start"
          variant="outline"
          aria-label="Cuộc trò chuyện mới"
        >
          <MessageSquarePlus className="w-4 h-4" />
          Cuộc trò chuyện mới
        </Button>
      </div>

      {/* List */}
      <nav className="flex-1 overflow-y-auto p-2 space-y-0.5">
        {loading && (
          <div className="space-y-1.5 px-1 pt-1">
            {[1, 2, 3].map((n) => (
              <div
                key={n}
                className="h-9 rounded-lg bg-muted/60 animate-pulse"
              />
            ))}
          </div>
        )}

        {!loading && conversations.length === 0 && (
          <p className="px-3 py-6 text-xs text-muted-foreground text-center">
            Chưa có cuộc trò chuyện nào.
          </p>
        )}

        {conversations.map((conv) => (
          <div
            key={conv.id}
            className={cn(
              'group flex items-center gap-1 rounded-lg px-2 py-2 text-sm cursor-pointer transition-colors',
              activeId === conv.id
                ? 'bg-primary/12 text-primary font-medium border border-primary/20'
                : 'text-muted-foreground hover:bg-muted hover:text-foreground'
            )}
            role="button"
            tabIndex={0}
            aria-current={activeId === conv.id ? 'page' : undefined}
            onClick={() => onSelect(conv.id)}
            onKeyDown={(e) => e.key === 'Enter' && onSelect(conv.id)}
          >
            <span className="flex-1 truncate leading-tight">{conv.title}</span>
            <button
              type="button"
              aria-label={`Xóa: ${conv.title}`}
              onClick={(e) => {
                e.stopPropagation()
                setConfirmId(conv.id)
              }}
              className="shrink-0 opacity-0 group-hover:opacity-100 rounded p-0.5 text-muted-foreground hover:text-destructive transition-all"
            >
              <Trash2 className="w-3.5 h-3.5" />
            </button>
          </div>
        ))}
      </nav>

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
