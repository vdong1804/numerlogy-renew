/**
 * ChatLayout — responsive 3-column shell: sidebar 280px | thread 1fr | citation drawer 360px.
 * Sidebar collapses to Sheet on mobile (<768px).
 * Wires all hooks and passes state down to parts.
 */

import { Menu, Sparkles } from 'lucide-react'
import { useCallback, useRef, useState } from 'react'
import { toast } from 'sonner'

import { Sheet, SheetContent } from '@/components/ui/sheet'
import { useUserAuth } from '@/lib/user-auth'
import type { Citation, Message } from '@/models/Chat'

import { useChatStream } from './hooks/use-chat-stream'
import { useConversations } from './hooks/use-conversations'
import { useMessages } from './hooks/use-messages'
import { usePdfUpload } from './hooks/use-pdf-upload'
import { useQuota } from './hooks/use-quota'
import { useRateLimitCountdown } from './hooks/use-rate-limit-countdown'
import ChatStartHero, { PROMPT_SUGGESTIONS } from './parts/ChatStartHero'
import CitationDrawer from './parts/CitationDrawer'
import ConversationSidebar from './parts/ConversationSidebar'
import MessageInput from './parts/MessageInput'
import MessageThread from './parts/MessageThread'
import QuotaBadge from './parts/QuotaBadge'
import UpsellModal from './parts/UpsellModal'

export default function ChatLayout() {
  const { user } = useUserAuth()
  const [activeConvId, setActiveConvId] = useState<number | null>(null)
  const [inputText, setInputText] = useState('')
  const [activeCitation, setActiveCitation] = useState<Citation | null>(null)
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false)
  const [upsellOpen, setUpsellOpen] = useState(false)

  const { quota, refresh: refreshQuota } = useQuota()
  const rateLimit = useRateLimitCountdown()
  // Monotone negative counter for optimistic message ids.
  // Negative ids are local-only and replaced when the persisted message arrives.
  const optimisticIdRef = useRef(-1)

  const {
    conversations,
    loading: convsLoading,
    create,
    remove,
  } = useConversations()
  const { messages, loading: msgsLoading, append } = useMessages(activeConvId)
  const {
    attachment,
    uploading,
    error: uploadError,
    upload,
    clear: clearPdf,
  } = usePdfUpload(activeConvId)

  const handleMessageComplete = useCallback(
    (msg: Message) => {
      append(msg)
    },
    [append]
  )

  // Stable callback identity — avoids re-creating send closure on every render (H2).
  const handleQuotaExceeded = useCallback(() => setUpsellOpen(true), [])

  const handleRateLimited = useCallback(
    (retryAfter: number, reason: 'bucket_empty' | 'daily_cap') => {
      rateLimit.trigger(retryAfter, reason)
      if (reason === 'daily_cap') {
        toast.error(
          'Bạn đã đạt giới hạn tin nhắn hôm nay. Thử lại vào ngày mai.',
          {
            duration: 8000,
          }
        )
      } else {
        toast.warning(
          `Bạn gửi tin nhắn quá nhanh. Vui lòng đợi ${retryAfter} giây.`,
          { duration: 3000 }
        )
      }
    },
    [rateLimit]
  )

  const {
    send,
    streamingText,
    streamingCitations,
    isStreaming,
    error: streamError,
    cancel,
  } = useChatStream(activeConvId, handleMessageComplete, {
    onQuotaExceeded: handleQuotaExceeded,
    onRateLimited: handleRateLimited,
  })

  const handleSend = useCallback(async () => {
    const text = inputText.trim()
    if (!text || !activeConvId) return

    optimisticIdRef.current -= 1
    const userMsg: Message = {
      id: optimisticIdRef.current,
      role: 'user',
      content: text,
      citations: [],
      createdAt: new Date().toISOString(),
    }
    append(userMsg)
    setInputText('')

    await send(text, attachment?.pdfContextId)
    rateLimit.clear()
    refreshQuota().catch(() => undefined)
  }, [inputText, activeConvId, append, send, attachment, refreshQuota])

  const handleCreate = useCallback(async () => {
    const conv = await create()
    setActiveConvId(conv.id)
    setMobileSidebarOpen(false)
  }, [create])

  const handleSelect = useCallback((id: number) => {
    setActiveConvId(id)
    setMobileSidebarOpen(false)
  }, [])

  const handleCitationClick = useCallback(
    (index: number) => {
      const allCitations = [
        ...streamingCitations,
        ...messages.flatMap((m) => m.citations),
      ]
      const found = allCitations.find((c) => c.index === index) ?? null
      setActiveCitation(found)
      setDrawerOpen(true)
    },
    [streamingCitations, messages]
  )

  // Pre-fill a suggested prompt into the input box (welcome screen quick start).
  const handlePickSuggestion = useCallback(
    async (text: string) => {
      let convId = activeConvId
      if (convId == null) {
        const conv = await create()
        convId = conv.id
        setActiveConvId(convId)
      }
      setInputText(text)
    },
    [activeConvId, create]
  )

  const sidebar = (
    <ConversationSidebar
      conversations={conversations}
      activeId={activeConvId}
      loading={convsLoading}
      user={user}
      onSelect={handleSelect}
      onCreate={handleCreate}
      onDelete={remove}
    />
  )

  // Subtle radial glow on main thread for visual depth
  const threadBgStyle = {
    backgroundImage:
      'radial-gradient(circle at 12% -5%, hsla(243, 75%, 65%, 0.10) 0%, transparent 45%),' +
      'radial-gradient(circle at 95% 100%, hsla(18, 95%, 58%, 0.06) 0%, transparent 40%)',
  }

  return (
    <div className="flex h-full w-full overflow-hidden bg-background text-foreground">
      {/* Desktop sidebar */}
      <div className="hidden md:flex w-[280px] shrink-0 flex-col border-r border-border bg-card/30">
        {sidebar}
      </div>

      {/* Mobile sidebar via Sheet */}
      <Sheet open={mobileSidebarOpen} onOpenChange={setMobileSidebarOpen}>
        <SheetContent side="left" className="w-[300px] p-0">
          {sidebar}
        </SheetContent>
      </Sheet>

      {/* Main thread */}
      <div
        className="flex flex-col flex-1 min-w-0 relative"
        style={threadBgStyle}
      >
        {/* Topbar — slim brand bar; conversation title lives in sidebar to avoid duplication */}
        <div className="flex items-center gap-3 px-4 h-12 border-b border-border/60 bg-card/30 backdrop-blur-sm shrink-0">
          <button
            type="button"
            aria-label="Mở danh sách cuộc trò chuyện"
            onClick={() => setMobileSidebarOpen(true)}
            className="md:hidden p-1.5 rounded-md text-muted-foreground hover:bg-muted transition-colors"
          >
            <Menu className="w-5 h-5" />
          </button>
          <div className="flex items-center gap-2 flex-1 min-w-0">
            <span className="inline-flex items-center justify-center w-6 h-6 rounded-md bg-primary/15 text-primary shrink-0">
              <Sparkles className="w-3.5 h-3.5" aria-hidden="true" />
            </span>
            <span className="text-sm font-semibold truncate">
              Trợ lý AI Numerology
            </span>
          </div>
          {quota && (
            <QuotaBadge quota={quota} onExhausted={() => setUpsellOpen(true)} />
          )}
        </div>

        {/* No conversation selected — welcome screen */}
        {!activeConvId ? (
          <div className="flex-1 overflow-y-auto">
            <ChatStartHero
              heading="Chào mừng đến Trợ lý AI"
              subheading="Hỏi đáp về thần số học, biểu đồ ngày sinh, ý nghĩa các con số và nhiều hơn nữa. Chọn một gợi ý để bắt đầu nhanh."
              suggestions={PROMPT_SUGGESTIONS}
              primaryAction={{
                label: 'Tạo cuộc trò chuyện mới',
                onClick: handleCreate,
              }}
              onPickSuggestion={handlePickSuggestion}
            />
          </div>
        ) : (
          <>
            {streamError && (
              <div
                role="alert"
                className="mx-4 mt-2 rounded-lg bg-destructive/10 border border-destructive/20 px-3 py-2 text-xs text-destructive"
              >
                {streamError}
              </div>
            )}

            <MessageThread
              messages={messages}
              loading={msgsLoading}
              streamingText={streamingText}
              isStreaming={isStreaming}
              onCitationClick={handleCitationClick}
              onPickSuggestion={(t) => setInputText(t)}
            />

            <MessageInput
              value={inputText}
              onChange={setInputText}
              onSend={handleSend}
              onCancel={cancel}
              isStreaming={isStreaming}
              disabled={msgsLoading}
              pdfFilename={attachment?.filename ?? null}
              pdfUploading={uploading}
              pdfError={uploadError}
              onPdfSelect={upload}
              onPdfRemove={clearPdf}
              quotaCanSend={quota?.canSend ?? true}
              rateLimitActive={rateLimit.active}
              rateLimitSecondsLeft={rateLimit.secondsLeft}
            />
          </>
        )}
      </div>

      {/* Citation drawer */}
      <CitationDrawer
        citation={activeCitation}
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
      />

      {/* Upsell modal — quota exhausted */}
      <UpsellModal
        open={upsellOpen}
        onClose={() => {
          setUpsellOpen(false)
          refreshQuota().catch(() => undefined)
        }}
      />
    </div>
  )
}
