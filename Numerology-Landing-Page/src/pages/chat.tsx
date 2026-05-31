/**
 * /chat page — entry point.
 * Guards: redirects to /login if not authenticated.
 * Renders ChatLayout inside the existing Main shell (Header + Footer).
 */

import Head from 'next/head'
import { useRouter } from 'next/router'
import { useEffect } from 'react'

import { Main } from '@/layouts/Main'
import { Meta } from '@/layouts/Meta'
import { useUserAuth } from '@/lib/user-auth'
import ChatLayout from '@/modules/chat/ChatLayout'

export default function ChatPage() {
  const { user, loading } = useUserAuth()
  const router = useRouter()

  useEffect(() => {
    if (!loading && !user) {
      router.replace(`/login?next=${encodeURIComponent('/chat')}`)
    }
  }, [loading, user, router])

  if (loading) {
    return (
      <Main
        meta={
          <Meta
            title="Chat AI · Numerology"
            description="Trợ lý AI Numerology"
          />
        }
      >
        <div className="flex items-center justify-center min-h-[60vh]">
          <p className="text-sm text-muted-foreground">Đang tải...</p>
        </div>
      </Main>
    )
  }

  if (!user) return null

  return (
    <>
      <Head>
        <title>Chat AI · Numerology</title>
        <meta
          name="description"
          content="Trợ lý AI Numerology — hỏi đáp về thần số học"
        />
      </Head>
      <Main
        meta={
          <Meta
            title="Chat AI · Numerology"
            description="Trợ lý AI Numerology"
          />
        }
      >
        <ChatLayout />
      </Main>
    </>
  )
}
