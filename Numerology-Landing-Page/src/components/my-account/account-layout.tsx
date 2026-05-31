/**
 * AccountLayout — sidebar + topbar + auth guard for /my-account/*.
 *
 * Redirects to /login when no token, shows a spinner while loading auth.
 * Header echoes the home page style: Philosopher heading + orange accent bar
 * + warm cosmic background gradients (configured in admin.css under .account-shell).
 */
import { useRouter } from 'next/router'
import { useEffect } from 'react'
import type { ReactNode } from 'react'

import { Main } from '@/layouts/Main'
import { Meta } from '@/layouts/Meta'
import { useUserAuth } from '@/lib/user-auth'
import AccountSidebarNav from './account-sidebar-nav'

interface Props {
  title: string
  description?: string
  children: ReactNode
}

export default function AccountLayout({ title, description, children }: Props) {
  const { user, loading } = useUserAuth()
  const router = useRouter()

  useEffect(() => {
    if (!loading && !user) {
      router.replace(`/login?next=${encodeURIComponent(router.asPath)}`)
    }
  }, [loading, user, router])

  if (loading || !user) {
    return (
      <Main meta={<Meta title={title} description={description ?? title} />}>
        <div className="account-shell">
          <div className="min-h-[50vh] flex items-center justify-center">
            <p className="text-sm text-muted-foreground">Đang tải...</p>
          </div>
        </div>
      </Main>
    )
  }

  return (
    <Main meta={<Meta title={title} description={description ?? title} />}>
      <div className="account-shell min-h-[70vh]">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 py-8 grid grid-cols-1 md:grid-cols-[240px_1fr] gap-6 md:gap-8">
          <aside className="md:sticky md:top-24 md:self-start">
            <div className="rounded-2xl border border-border bg-card shadow-sm p-2">
              <AccountSidebarNav />
            </div>
          </aside>
          <section>
            <header className="mb-6">
              <h1 className="text-2xl sm:text-3xl font-bold tracking-tight">{title}</h1>
              <div className="h-[3px] w-12 bg-primary rounded-full mt-2" />
              {description && (
                <p className="text-sm text-muted-foreground mt-3">{description}</p>
              )}
            </header>
            {children}
          </section>
        </div>
      </div>
    </Main>
  )
}
