/**
 * Sidebar nav for /my-account.
 */
import Link from 'next/link'
import { useRouter } from 'next/router'
import {
  Download,
  FileText,
  KeyRound,
  LayoutDashboard,
  LogOut,
  Settings,
  ShoppingBag,
  Sparkles,
  User,
} from 'lucide-react'

import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import { useUserAuth } from '@/lib/user-auth'

const ITEMS = [
  { href: '/my-account', label: 'Tổng quan', icon: LayoutDashboard, exact: true },
  { href: '/my-account/new-report', label: 'Tạo báo cáo mới', icon: Sparkles, featured: true },
  { href: '/my-account/orders', label: 'Đơn hàng', icon: ShoppingBag },
  { href: '/my-account/reports', label: 'Báo cáo của tôi', icon: FileText },
  { href: '/my-account/downloads', label: 'Lịch sử tải', icon: Download },
  { href: '/my-account/profile', label: 'Hồ sơ', icon: User },
  { href: '/my-account/password', label: 'Đổi mật khẩu', icon: KeyRound },
  { href: '/my-account/settings', label: 'Thông báo', icon: Settings },
]

export default function AccountSidebarNav() {
  const router = useRouter()
  const { logout } = useUserAuth()

  return (
    <nav className="flex flex-col gap-1 text-sm">
      {ITEMS.map((item) => {
        const Icon = item.icon
        const active = item.exact
          ? router.pathname === item.href
          : router.pathname.startsWith(item.href)
        return (
          <Link
            key={item.href}
            href={item.href}
            className={cn(
              'flex items-center gap-2 rounded-lg px-3 py-2 text-sm transition-all',
              active
                ? 'bg-primary/12 text-primary font-semibold shadow-sm border border-primary/20'
                : item.featured
                ? 'bg-gradient-to-r from-primary/8 to-secondary/8 text-foreground font-medium border border-primary/15 hover:from-primary/15 hover:to-secondary/15'
                : 'text-muted-foreground hover:bg-muted hover:text-foreground'
            )}
          >
            <Icon className="w-4 h-4" />
            {item.label}
          </Link>
        )
      })}
      <div className="border-t border-border mt-2 pt-2">
        <Button variant="ghost" className="w-full justify-start" onClick={() => logout()}>
          <LogOut className="w-4 h-4" /> Đăng xuất
        </Button>
      </div>
    </nav>
  )
}
