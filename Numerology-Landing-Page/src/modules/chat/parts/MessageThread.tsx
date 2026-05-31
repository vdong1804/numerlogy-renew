/**
 * MessageThread — renders message history + streaming assistant bubble.
 * Auto-scrolls to bottom only when near bottom; shows a pill to scroll
 * when user has scrolled away mid-stream.
 * TODO: add react-window virtualization if conversation exceeds 100 messages.
 */

import { useCallback, useEffect, useRef, useState } from 'react'

import { Skeleton } from '@/components/ui/skeleton'
import { cn } from '@/lib/utils'
import type { Message } from '@/models/Chat'

import MessageMarkdown from './MessageMarkdown'

/** Threshold in pixels — within this distance from bottom = "near bottom" */
const NEAR_BOTTOM_PX = 80

interface MessageThreadProps {
  messages: Message[]
  loading: boolean
  streamingText: string
  isStreaming: boolean
  onCitationClick: (index: number) => void
}

// ---------------------------------------------------------------------------
// Sub-components defined first to satisfy no-use-before-define
// ---------------------------------------------------------------------------

function AssistantAvatar() {
  return (
    <div
      aria-hidden="true"
      className="shrink-0 w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center text-xs font-bold text-primary"
    >
      AI
    </div>
  )
}

function UserAvatar() {
  return (
    <div
      aria-hidden="true"
      className="shrink-0 w-8 h-8 rounded-full bg-muted flex items-center justify-center text-xs font-bold text-muted-foreground"
    >
      Tôi
    </div>
  )
}

function MessageBubble({
  message,
  onCitationClick,
}: {
  message: Message
  onCitationClick: (index: number) => void
}) {
  const isUser = message.role === 'user'

  return (
    <div className={cn('flex gap-3', isUser && 'flex-row-reverse')}>
      {isUser ? <UserAvatar /> : <AssistantAvatar />}
      <div
        className={cn(
          'max-w-[80%] rounded-2xl px-4 py-3 text-sm',
          isUser
            ? 'bg-primary text-primary-foreground rounded-tr-sm'
            : 'bg-muted text-foreground rounded-tl-sm'
        )}
      >
        {isUser ? (
          <p className="whitespace-pre-wrap leading-relaxed">
            {message.content}
          </p>
        ) : (
          <MessageMarkdown
            content={message.content}
            onCitationClick={onCitationClick}
          />
        )}

        {/* Citation badges for completed messages */}
        {message.citations.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-2 pt-2 border-t border-border/30">
            {message.citations.map((c) => (
              <button
                key={c.index}
                type="button"
                aria-label={`Xem trích dẫn ${c.index}: ${
                  c.title ?? c.sourceType
                }`}
                onClick={() => onCitationClick(c.index)}
                className="inline-flex items-center gap-1 rounded-full bg-background/30 border border-border/50 px-2 py-0.5 text-xs hover:bg-background/50 transition-colors"
              >
                <span className="font-bold">[{c.index}]</span>
                <span className="truncate max-w-[100px] text-muted-foreground">
                  {c.title ?? c.sourceType}
                </span>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Main export
// ---------------------------------------------------------------------------

export default function MessageThread({
  messages,
  loading,
  streamingText,
  isStreaming,
  onCitationClick,
}: MessageThreadProps) {
  const bottomRef = useRef<HTMLDivElement>(null)
  const scrollContainerRef = useRef<HTMLDivElement>(null)
  const [isNearBottom, setIsNearBottom] = useState(true)

  // Track whether user is near the bottom of the scroll container
  const handleScroll = useCallback(() => {
    const el = scrollContainerRef.current
    if (!el) return
    const nearBottom =
      el.scrollHeight - el.scrollTop - el.clientHeight < NEAR_BOTTOM_PX
    setIsNearBottom(nearBottom)
  }, [])

  // Auto-scroll only when near bottom; otherwise show the "new messages" pill
  useEffect(() => {
    if (isNearBottom) {
      bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
    }
  }, [messages.length, streamingText, isNearBottom])

  // Must be before early return to comply with rules-of-hooks
  const scrollToBottom = useCallback(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
    setIsNearBottom(true)
  }, [])

  if (loading) {
    return (
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {[1, 2, 3].map((n) => (
          <div
            key={n}
            className={cn('flex gap-3', n % 2 === 0 && 'flex-row-reverse')}
          >
            <Skeleton className="w-8 h-8 rounded-full shrink-0" />
            <Skeleton
              className={cn('h-16 rounded-xl', n % 2 === 0 ? 'w-48' : 'w-64')}
            />
          </div>
        ))}
      </div>
    )
  }

  return (
    <div className="flex-1 relative overflow-hidden">
      <div
        ref={scrollContainerRef}
        onScroll={handleScroll}
        className="h-full overflow-y-auto p-4 space-y-4"
        role="log"
        aria-live="polite"
        aria-label="Lịch sử trò chuyện"
      >
        {messages.length === 0 && !isStreaming && (
          <div className="flex flex-col items-center justify-center h-full min-h-[200px] text-center px-4">
            <p className="text-2xl mb-2">💬</p>
            <p className="text-sm font-medium text-muted-foreground">
              Bắt đầu cuộc trò chuyện bằng cách nhập câu hỏi bên dưới.
            </p>
          </div>
        )}

        {/* History messages */}
        {messages.map((msg) => (
          <MessageBubble
            key={msg.id}
            message={msg}
            onCitationClick={onCitationClick}
          />
        ))}

        {/* Streaming assistant bubble */}
        {isStreaming && streamingText && (
          <div className="flex gap-3">
            <AssistantAvatar />
            <div className="max-w-[80%] rounded-2xl rounded-tl-sm bg-muted px-4 py-3 text-sm">
              <MessageMarkdown
                content={streamingText}
                onCitationClick={onCitationClick}
              />
              <span className="inline-block w-1.5 h-4 bg-primary/70 animate-pulse ml-0.5 align-middle" />
            </div>
          </div>
        )}

        {/* Waiting for first token */}
        {isStreaming && !streamingText && (
          <div className="flex gap-3">
            <AssistantAvatar />
            <div className="rounded-2xl rounded-tl-sm bg-muted px-4 py-3">
              <div className="flex gap-1 items-center h-5">
                {[0, 1, 2].map((i) => (
                  <span
                    key={i}
                    className="w-1.5 h-1.5 rounded-full bg-muted-foreground/50 animate-bounce"
                    style={{ animationDelay: `${i * 150}ms` }}
                  />
                ))}
              </div>
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* "New messages" pill — shown when user scrolled away mid-stream */}
      {isStreaming && !isNearBottom && (
        <button
          type="button"
          onClick={scrollToBottom}
          className="absolute bottom-4 right-4 flex items-center gap-1.5 rounded-full bg-primary text-primary-foreground px-3 py-1.5 text-xs font-medium shadow-md hover:bg-primary/90 transition-colors"
          aria-label="Cuộn xuống tin nhắn mới"
        >
          ↓ Có tin nhắn mới
        </button>
      )}
    </div>
  )
}
