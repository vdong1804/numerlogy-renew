/**
 * Cmd+K command palette: navigate, theme toggle, logout.
 */
import * as React from 'react'
import { useRouter } from 'next/router'
import { useTheme } from 'next-themes'
import { LogOut, Moon, Sun, ArrowRight } from 'lucide-react'

import {
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandSeparator,
  CommandShortcut,
} from '@/components/ui/command'
import { ADMIN_NAV_GROUPS, ADMIN_DASHBOARD_ITEM, ADMIN_DASHBOARD_ICON } from './admin-nav-config'

interface AdminCommandPaletteProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onLogout?: () => void
}

export function AdminCommandPalette({ open, onOpenChange, onLogout }: AdminCommandPaletteProps) {
  const router = useRouter()
  const { setTheme, resolvedTheme } = useTheme()

  const go = (href: string) => {
    onOpenChange(false)
    router.push(href)
  }

  return (
    <CommandDialog open={open} onOpenChange={onOpenChange}>
      <CommandInput placeholder="Tìm trang, hành động, nội dung..." />
      <CommandList>
        <CommandEmpty>Không tìm thấy kết quả.</CommandEmpty>

        <CommandGroup heading="Điều hướng">
          <CommandItem onSelect={() => go(ADMIN_DASHBOARD_ITEM.href)}>
            <ADMIN_DASHBOARD_ICON className="text-muted-foreground" />
            <span>{ADMIN_DASHBOARD_ITEM.label}</span>
            <CommandShortcut>↵</CommandShortcut>
          </CommandItem>

          {ADMIN_NAV_GROUPS.map((group) => {
            const first = group.items[0]
            if (group.items.length !== 1 || !first) return null
            return (
              <CommandItem key={group.id} onSelect={() => go(first.href)}>
                <group.icon className="text-muted-foreground" />
                <span>{group.label}</span>
                <ArrowRight className="ml-auto h-3 w-3 text-muted-foreground/60" />
              </CommandItem>
            )
          })}
        </CommandGroup>

        <CommandSeparator />

        <CommandGroup heading="Nội dung Thần Số Học">
          {ADMIN_NAV_GROUPS.find((g) => g.id === 'content')?.items.map((item) => (
            <CommandItem
              key={item.href}
              onSelect={() => go(item.href)}
              keywords={[item.label, item.description ?? '']}
            >
              <span className="w-1.5 h-1.5 rounded-full bg-primary/60 mr-1" />
              <span>{item.label}</span>
              <span className="ml-auto text-[11px] text-muted-foreground font-mono">
                {item.href.replace('/admin/content/', '')}
              </span>
            </CommandItem>
          ))}
        </CommandGroup>

        <CommandSeparator />

        <CommandGroup heading="Hành động">
          <CommandItem
            onSelect={() => {
              setTheme(resolvedTheme === 'dark' ? 'light' : 'dark')
              onOpenChange(false)
            }}
          >
            {resolvedTheme === 'dark' ? <Sun /> : <Moon />}
            <span>
              {resolvedTheme === 'dark' ? 'Chuyển sang sáng' : 'Chuyển sang tối'}
            </span>
          </CommandItem>
          {onLogout && (
            <CommandItem
              onSelect={() => {
                onOpenChange(false)
                onLogout()
              }}
            >
              <LogOut className="text-destructive" />
              <span className="text-destructive">Đăng xuất</span>
            </CommandItem>
          )}
        </CommandGroup>
      </CommandList>
    </CommandDialog>
  )
}
