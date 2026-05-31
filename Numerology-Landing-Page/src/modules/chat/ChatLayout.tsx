/**
 * ChatLayout — responsive 3-column shell: sidebar 260px | thread 1fr | citation drawer 320px.
 * Sidebar collapses to Sheet on mobile (<768px).
 * Wires all hooks and passes state down to parts.
 */

import { Menu } from 'lucide-react'
import { useCallback, useRef, useState } from 'react'
import { toast } from 'sonner'

import { Sheet, SheetContent } from '@/components/ui/sheet'
import type { Citation, Message } from '@/models/Chat'

import { useChatStream } from './hooks/use-chat-stream'
import { useConversations } from './hooks/use-conversations'
import { useMessages } from './hooks/use-messages'
import { usePdfUpload } from './hooks/use-pdf-upload'
import { useQuota } from './hooks/use-quota'
import { useRateLimitCountdown } from './hooks/use-rate-limit-countdown'
import CitationDrawer from './parts/CitationDrawer'
import ConversationSidebar from './parts/ConversationSidebar'
import MessageInput from './parts/MessageInput'
import MessageThread from './parts/MessageThread'
import QuotaBadge from './parts/QuotaBadge'
import UpsellModal from './parts/UpsellModal'

export default function ChatLayout() {
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

    // Optimistically append user message with a negative sentinel id.
    // Negative ids are local-only; replaced when the persisted message arrives.
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
    // Clear any active rate-limit countdown on successful send
    rateLimit.clear()
    // Refresh quota after each send so badge stays current
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
      // Find citation from streaming or from last completed message
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

  const sidebar = (
    <ConversationSidebar
      conversations={conversations}
      activeId={activeConvId}
      loading={convsLoading}
      onSelect={handleSelect}
      onCreate={handleCreate}
      onDelete={remove}
    />
  )

  return (
    <div className="flex h-[calc(100dvh-64px)] overflow-hidden">
      {/* Desktop sidebar */}
      <div className="hidden md:flex w-[260px] shrink-0 flex-col">
        {sidebar}
      </div>

      {/* Mobile sidebar via Sheet */}
      <Sheet open={mobileSidebarOpen} onOpenChange={setMobileSidebarOpen}>
        <SheetContent side="left" className="w-[260px] p-0">
          {sidebar}
        </SheetContent>
      </Sheet>

      {/* Main thread */}
      <div className="flex flex-col flex-1 min-w-0 bg-background">
        {/* Mobile topbar */}
        <div className="md:hidden flex items-center gap-2 px-3 py-2 border-b border-border bg-card">
          <button
            type="button"
            aria-label="Mở danh sách cuộc trò chuyện"
            onClick={() => setMobileSidebarOpen(true)}
            className="p-1.5 rounded-md text-muted-foreground hover:bg-muted transition-colors"
          >
            <Menu className="w-5 h-5" />
          </button>
          <span className="text-sm font-medium truncate flex-1">
            {conversations.find((c) => c.id === activeConvId)?.title ??
              'Chat AI'}
          </span>
          {quota && (
            <QuotaBadge quota={quota} onExhausted={() => setUpsellOpen(true)} />
          )}
        </div>

        {/* Desktop quota badge row — only when a conversation is active */}
        {activeConvId && quota && (
          <div className="hidden md:flex items-center justify-end px-4 pt-2 pb-0">
            <QuotaBadge quota={quota} onExhausted={() => setUpsellOpen(true)} />
          </div>
        )}

        {/* No conversation selected */}
        {!activeConvId ? (
          <div className="flex-1 flex items-center justify-center p-8 text-center">
            <div>
              <p className="text-3xl mb-3">✨</p>
              <p className="font-semibold text-lg mb-1">
                Chào mừng đến Trợ lý AI
              </p>
              <p className="text-sm text-muted-foreground max-w-xs">
                Chọn một cuộc trò chuyện hoặc tạo mới để bắt đầu.
              </p>
            </div>
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
