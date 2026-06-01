/**
 * /chat page — entry point.
 * Guards: redirects to /login if not authenticated.
 * Renders Header (no Footer) and wraps chat in `.account-shell.dark` so
 * shadcn-style CSS variables resolve to the dark theme that matches the
 * site identity. Body padding/scroll is neutralized while mounted so the
 * chat workspace fills the viewport below the header.
 */

import Head from 'next/head'
import { useRouter } from 'next/router'
import { useEffect } from 'react'

import Header from '@/layouts/Header'
import { Meta } from '@/layouts/Meta'
import { useUserAuth } from '@/lib/user-auth'
import ChatLayout from '@/modules/chat/ChatLayout'

/**
 * Lock body to the viewport while chat is mounted so:
 *  - main.scss's `padding-top: 93px` is neutralized (header is fixed, so we
 *    apply our own offset via the wrapper instead).
 *  - body cannot scroll → no Footer/page-bg bleed under the chat workspace.
 */
function useChatBodyLock() {
  useEffect(() => {
    const { body } = document
    const prev = {
      overflow: body.style.overflow,
      paddingTop: body.style.paddingTop,
      backgroundColor: body.style.backgroundColor,
    }
    body.style.overflow = 'hidden'
    body.style.paddingTop = '0'
    // hsl(222 47% 7%) — same as .account-shell.dark --background, prevents
    // the legacy dark-blue site bg from flashing through.
    body.style.backgroundColor = 'hsl(222, 47%, 7%)'
    return () => {
      body.style.overflow = prev.overflow
      body.style.paddingTop = prev.paddingTop
      body.style.backgroundColor = prev.backgroundColor
    }
  }, [])
}

export default function ChatPage() {
  const { user, loading } = useUserAuth()
  const router = useRouter()
  useChatBodyLock()

  useEffect(() => {
    if (!loading && !user) {
      router.replace(`/login?next=${encodeURIComponent('/chat')}`)
    }
  }, [loading, user, router])

  return (
    <>
      <Head>
        <title>Chat AI · Numerology</title>
        <meta
          name="description"
          content="Trợ lý AI Numerology — hỏi đáp về thần số học"
        />
      </Head>
      <Meta title="Chat AI · Numerology" description="Trợ lý AI Numerology" />
      <Header />
      <div
        className="account-shell dark fixed inset-x-0 bottom-0 top-[93px] overflow-hidden"
        style={{ backgroundColor: 'hsl(222, 47%, 7%)' }}
      >
        {loading || !user ? (
          <div className="flex items-center justify-center h-full">
            <p className="text-sm text-muted-foreground">Đang tải...</p>
          </div>
        ) : (
          <ChatLayout />
        )}
      </div>
    </>
  )
}
