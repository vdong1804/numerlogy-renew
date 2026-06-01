/**
 * MessageThread — renders message history + streaming assistant bubble.
 * Auto-scrolls to bottom only when near bottom; shows a pill to scroll
 * when user has scrolled away mid-stream.
 * TODO: add react-window virtualization if conversation exceeds 100 messages.
 */

import { Bot, ChevronDown, User } from 'lucide-react'
import { useCallback, useEffect, useRef, useState } from 'react'

import { Skeleton } from '@/components/ui/skeleton'
import { cn } from '@/lib/utils'
import type { Message } from '@/models/Chat'

import ChatStartHero, { PROMPT_SUGGESTIONS } from './ChatStartHero'
import MessageMarkdown from './MessageMarkdown'

/** Threshold in pixels — within this distance from bottom = "near bottom" */
const NEAR_BOTTOM_PX = 80

interface MessageThreadProps {
  messages: Message[]
  loading: boolean
  streamingText: string
  isStreaming: boolean
  onCitationClick: (index: number) => void
  /** Optional — let parent prefill input from suggested prompts */
  onPickSuggestion?: (text: string) => void
}

// ---------------------------------------------------------------------------
// Sub-components defined first to satisfy no-use-before-define
// ---------------------------------------------------------------------------

function AssistantAvatar() {
  return (
    <div
      aria-hidden="true"
      className="shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-primary to-primary/70 flex items-center justify-center text-primary-foreground shadow-sm"
    >
      <Bot className="w-4 h-4" />
    </div>
  )
}

function UserAvatar() {
  return (
    <div
      aria-hidden="true"
      className="shrink-0 w-8 h-8 rounded-full bg-muted border border-border flex items-center justify-center text-muted-foreground"
    >
      <User className="w-4 h-4" />
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
    <div className={cn('flex gap-3 group', isUser && 'flex-row-reverse')}>
      {isUser ? <UserAvatar /> : <AssistantAvatar />}
      <div
        className={cn(
          'max-w-[78%] rounded-2xl px-4 py-2.5 text-sm shadow-sm',
          isUser
            ? 'bg-primary text-primary-foreground rounded-tr-md'
            : 'bg-card border border-border text-foreground rounded-tl-md'
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
          <div className="flex flex-wrap gap-1.5 mt-2.5 pt-2.5 border-t border-border/50">
            {message.citations.map((c) => (
              <button
                key={c.index}
                type="button"
                aria-label={`Xem trích dẫn ${c.index}: ${
                  c.title ?? c.sourceType
                }`}
                onClick={() => onCitationClick(c.index)}
                className="inline-flex items-center gap-1 rounded-full bg-muted hover:bg-muted/70 border border-border/60 px-2 py-0.5 text-xs transition-colors"
              >
                <span className="font-semibold text-primary">[{c.index}]</span>
                <span className="truncate max-w-[120px] text-muted-foreground">
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
  onPickSuggestion,
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
      <div className="flex-1 overflow-y-auto px-4 py-6 space-y-5">
        {[1, 2, 3].map((n) => (
          <div
            key={n}
            className={cn('flex gap-3', n % 2 === 0 && 'flex-row-reverse')}
          >
            <Skeleton className="w-8 h-8 rounded-full shrink-0" />
            <Skeleton
              className={cn('h-16 rounded-2xl', n % 2 === 0 ? 'w-48' : 'w-64')}
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
        className="h-full overflow-y-auto"
        role="log"
        aria-live="polite"
        aria-label="Lịch sử trò chuyện"
      >
        {/* Empty conversation — centered hero with suggestion grid.
            ChatStartHero internally uses min-h-full + flex to fill the
            scroll viewport and center its content both axes. */}
        {messages.length === 0 && !isStreaming && onPickSuggestion && (
          <ChatStartHero
            heading="Bắt đầu cuộc trò chuyện"
            subheading="Nhập câu hỏi vào ô bên dưới hoặc chọn một gợi ý để khởi đầu."
            suggestions={PROMPT_SUGGESTIONS}
            onPickSuggestion={onPickSuggestion}
          />
        )}

        <div className="max-w-3xl mx-auto px-4 py-6 space-y-5">
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
              <div className="max-w-[78%] rounded-2xl rounded-tl-md bg-card border border-border px-4 py-2.5 text-sm shadow-sm">
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
              <div className="rounded-2xl rounded-tl-md bg-card border border-border px-4 py-3 shadow-sm">
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
      </div>

      {/* "New messages" pill — shown when user scrolled away mid-stream */}
      {isStreaming && !isNearBottom && (
        <button
          type="button"
          onClick={scrollToBottom}
          className="absolute bottom-4 left-1/2 -translate-x-1/2 inline-flex items-center gap-1.5 rounded-full bg-primary text-primary-foreground px-3 py-1.5 text-xs font-medium shadow-lg hover:bg-primary/90 transition-colors"
          aria-label="Cuộn xuống tin nhắn mới"
        >
          <ChevronDown className="w-3.5 h-3.5" />
          Tin nhắn mới
        </button>
      )}
    </div>
  )
}
