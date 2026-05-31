/**
 * Admin layout shell — sidebar + topbar + auth guard + command palette + dark mode.
 * Mobile: sidebar hidden by default, opens via Sheet from topbar hamburger.
 */
import * as React from 'react'
import Head from 'next/head'

import { Sheet, SheetContent } from '@/components/ui/sheet'
import { useAdminAuth } from '@/lib/admin-auth'

import { AdminCommandPalette } from './admin-command-palette'
import { AdminSidebarNav } from './admin-sidebar-nav'
import { AdminThemeProvider } from './admin-theme-provider'
import { AdminTopbar } from './admin-topbar'
import { ToastProvider } from './admin-toast'

interface AdminLayoutProps {
  children: React.ReactNode
  title?: string
}

export default function AdminLayout({ children, title }: AdminLayoutProps) {
  const { user, loading, logout } = useAdminAuth()
  const [mobileNavOpen, setMobileNavOpen] = React.useState(false)
  const [cmdOpen, setCmdOpen] = React.useState(false)

  // Cmd/Ctrl+K to open command palette
  React.useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.key === 'k' || e.key === 'K') && (e.metaKey || e.ctrlKey)) {
        e.preventDefault()
        setCmdOpen((v) => !v)
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [])

  if (loading) {
    return (
      <AdminThemeProvider>
        <div className="admin-shell min-h-screen flex items-center justify-center bg-background">
          <div className="flex flex-col items-center gap-3 text-muted-foreground text-sm">
            <span className="w-8 h-8 rounded-full border-2 border-primary/30 border-t-primary animate-spin" />
            Đang tải...
          </div>
        </div>
      </AdminThemeProvider>
    )
  }

  if (!user) return null

  return (
    <AdminThemeProvider>
      <Head>{title && <title>{`${title} · Admin Numerology`}</title>}</Head>
      <div className="admin-shell min-h-screen bg-background admin-gradient-mesh">
        <div className="flex min-h-screen">
          {/* Desktop sidebar */}
          <aside className="hidden md:flex md:flex-col w-64 shrink-0">
            <div className="sticky top-0 h-screen">
              <AdminSidebarNav />
            </div>
          </aside>

          {/* Mobile sidebar */}
          <Sheet open={mobileNavOpen} onOpenChange={setMobileNavOpen}>
            <SheetContent side="left" className="p-0 w-72">
              <AdminSidebarNav onNavigate={() => setMobileNavOpen(false)} />
            </SheetContent>
          </Sheet>

          {/* Main column */}
          <div className="flex-1 flex flex-col min-w-0">
            <AdminTopbar
              user={user}
              title={title}
              onOpenMobileSidebar={() => setMobileNavOpen(true)}
              onOpenCommandPalette={() => setCmdOpen(true)}
              onLogout={logout}
            />
            <main className="flex-1 p-4 sm:p-6 lg:p-8 animate-fade-in">{children}</main>
          </div>
        </div>

        <AdminCommandPalette open={cmdOpen} onOpenChange={setCmdOpen} onLogout={logout} />
        <ToastProvider />
      </div>
    </AdminThemeProvider>
  )
}
