/**
 * Admin topbar — hamburger (mobile), search trigger, theme toggle, user menu.
 */
import * as React from 'react'
import { LogOut, Menu, Search, User } from 'lucide-react'

import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import type { AdminUser } from '@/lib/admin-auth'

import { AdminBreadcrumbs } from './admin-breadcrumbs'
import { AdminThemeToggle } from './admin-theme-toggle'

interface AdminTopbarProps {
  user: AdminUser
  title?: string
  onOpenMobileSidebar: () => void
  onOpenCommandPalette: () => void
  onLogout: () => void
}

export function AdminTopbar({
  user,
  title,
  onOpenMobileSidebar,
  onOpenCommandPalette,
  onLogout,
}: AdminTopbarProps) {
  const initials = (user.full_name || user.email)
    .split(/\s+/)
    .map((s) => s[0])
    .slice(0, 2)
    .join('')
    .toUpperCase()

  return (
    <header className="sticky top-0 z-30 h-16 bg-background/85 backdrop-blur-md border-b border-border">
      <div className="h-full px-4 sm:px-6 flex items-center gap-3">
        {/* Mobile menu */}
        <Button
          variant="ghost"
          size="icon"
          className="md:hidden text-muted-foreground"
          onClick={onOpenMobileSidebar}
          aria-label="Mở menu"
        >
          <Menu className="w-5 h-5" />
        </Button>

        {/* Title + breadcrumbs */}
        <div className="hidden md:flex flex-col">
          {title && <h1 className="text-base font-semibold leading-tight">{title}</h1>}
          <AdminBreadcrumbs className="text-xs" />
        </div>
        <div className="md:hidden flex-1">
          {title && <h1 className="text-sm font-semibold truncate">{title}</h1>}
        </div>

        <div className="ml-auto flex items-center gap-1.5 sm:gap-2">
          {/* Search trigger (Cmd+K) */}
          <button
            type="button"
            onClick={onOpenCommandPalette}
            className="hidden sm:inline-flex items-center gap-2 h-9 w-56 lg:w-72 px-3 rounded-md border border-input bg-background/60 text-sm text-muted-foreground hover:bg-accent/40 transition-colors"
          >
            <Search className="w-4 h-4" />
            <span className="flex-1 text-left">Tìm hoặc nhập lệnh...</span>
            <kbd className="px-1.5 py-0.5 rounded bg-muted text-[10px] font-mono">⌘K</kbd>
          </button>
          <Button
            variant="ghost"
            size="icon"
            className="sm:hidden text-muted-foreground"
            onClick={onOpenCommandPalette}
            aria-label="Tìm kiếm"
          >
            <Search className="w-4 h-4" />
          </Button>

          <AdminThemeToggle />

          {/* User menu */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <button
                type="button"
                className="flex items-center gap-2 h-9 pl-1 pr-2.5 rounded-full hover:bg-accent/60 transition-colors"
                aria-label="Tài khoản"
              >
                <span className="flex items-center justify-center w-7 h-7 rounded-full bg-gradient-to-br from-primary to-accent-foreground/70 text-primary-foreground text-xs font-semibold shadow-sm">
                  {initials || 'A'}
                </span>
                <span className="hidden md:inline text-xs text-muted-foreground max-w-[140px] truncate">
                  {user.email}
                </span>
              </button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-60">
              <DropdownMenuLabel>Tài khoản</DropdownMenuLabel>
              <div className="px-2.5 pb-2">
                <p className="text-sm font-medium truncate">{user.full_name || 'Quản trị viên'}</p>
                <p className="text-xs text-muted-foreground truncate">{user.email}</p>
              </div>
              <DropdownMenuSeparator />
              <DropdownMenuItem disabled>
                <User />
                <span>Hồ sơ</span>
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem
                onSelect={onLogout}
                className="text-destructive focus:bg-destructive/10 focus:text-destructive"
              >
                <LogOut />
                <span>Đăng xuất</span>
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>
    </header>
  )
}
