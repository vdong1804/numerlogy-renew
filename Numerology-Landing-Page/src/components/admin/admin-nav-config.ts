/**
 * Single source of truth for admin navigation: sidebar, command palette, breadcrumbs.
 * Icon names map to lucide-react icons (resolved in nav components).
 */
import {
  LayoutDashboard,
  Newspaper,
  Package,
  Landmark,
  Users,
  CreditCard,
  BookOpen,
  ShoppingBag,
  Receipt,
  Activity,
  Bot,
  type LucideIcon,
} from 'lucide-react'

import { CONTENT_RESOURCES } from '@/lib/content-resources'

export interface AdminNavItem {
  href: string
  label: string
  description?: string
  /** Match prefix on router.pathname for active state */
  matchPrefix?: string
}

export interface AdminNavGroup {
  id: string
  label: string
  icon: LucideIcon
  items: AdminNavItem[]
  /** If true, the group itself navigates (single-item group rendered as flat link) */
  collapsible?: boolean
}

export const ADMIN_DASHBOARD_ITEM: AdminNavItem = {
  href: '/admin',
  label: 'Tổng quan',
  description: 'Bảng điều khiển chính',
  matchPrefix: '/admin',
}

export const ADMIN_NAV_GROUPS: AdminNavGroup[] = [
  {
    id: 'content',
    label: 'Nội dung Thần Số Học',
    icon: BookOpen,
    collapsible: true,
    items: CONTENT_RESOURCES.map((r) => ({
      href: `/admin/content/${r.slug}`,
      label: r.label,
      description: `Slug: ${r.slug}`,
    })),
  },
  {
    id: 'news',
    label: 'Tin tức',
    icon: Newspaper,
    items: [{ href: '/admin/news', label: 'Tin tức', description: 'Quản lý bài viết' }],
  },
  {
    id: 'products',
    label: 'Sản phẩm',
    icon: ShoppingBag,
    items: [{ href: '/admin/products', label: 'Sản phẩm', description: 'Catalogue gói + báo cáo + combo' }],
  },
  {
    id: 'orders',
    label: 'Đơn hàng',
    icon: Receipt,
    items: [{ href: '/admin/orders', label: 'Đơn hàng', description: 'Quản lý giao dịch' }],
  },
  {
    id: 'webhook-events',
    label: 'Webhook Events',
    icon: Activity,
    items: [{ href: '/admin/webhook-events', label: 'Webhook Events', description: 'Log SePay' }],
  },
  {
    id: 'packages',
    label: 'Gói dịch vụ (cũ)',
    icon: Package,
    items: [{ href: '/admin/packages', label: 'Gói dịch vụ (cũ)', description: 'Cấu hình gói thanh toán legacy' }],
  },
  {
    id: 'banks',
    label: 'Ngân hàng',
    icon: Landmark,
    items: [{ href: '/admin/banks', label: 'Ngân hàng', description: 'Tài khoản nhận tiền' }],
  },
  {
    id: 'chatbot',
    label: 'Chatbot RAG',
    icon: Bot,
    collapsible: true,
    items: [
      { href: '/admin/chatbot', label: 'Tổng quan Chatbot', description: 'Thống kê + chi phí' },
      { href: '/admin/chatbot/kb', label: 'Knowledge Base', description: 'Upload PDF/DOCX/TXT' },
      { href: '/admin/chatbot/prompt', label: 'System Prompt', description: 'Override + lịch sử' },
      { href: '/admin/chatbot/conversations', label: 'Hội thoại', description: 'Duyệt lịch sử chat' },
      { href: '/admin/chatbot/analytics', label: 'Analytics chi tiết', description: 'Biểu đồ + chi phí theo ngày' },
    ],
  },
  {
    id: 'users',
    label: 'Người dùng',
    icon: Users,
    items: [{ href: '/admin/users', label: 'Người dùng', description: 'Khách hàng & quyền hạn' }],
  },
  {
    id: 'payments',
    label: 'Thanh toán',
    icon: CreditCard,
    items: [
      { href: '/admin/payments', label: 'Thanh toán chờ duyệt', description: 'Phê duyệt giao dịch' },
    ],
  },
]

export const ADMIN_DASHBOARD_ICON = LayoutDashboard

/** Flat list — used by command palette & breadcrumb resolution. */
export interface FlatNavEntry extends AdminNavItem {
  groupLabel?: string
  groupId?: string
  icon?: LucideIcon
}

export const FLAT_NAV: FlatNavEntry[] = [
  { ...ADMIN_DASHBOARD_ITEM, icon: ADMIN_DASHBOARD_ICON },
  ...ADMIN_NAV_GROUPS.flatMap((g) =>
    g.items.map((item) => ({
      ...item,
      groupLabel: g.label,
      groupId: g.id,
      icon: g.icon,
    }))
  ),
]
