/**
 * Dynamic breadcrumbs from router path + nav config.
 * Examples:
 *   /admin                              → Tổng quan
 *   /admin/users                        → Tổng quan / Người dùng
 *   /admin/users/[id]                   → Tổng quan / Người dùng / #ID
 *   /admin/content/main-number          → Tổng quan / Nội dung / Số Chủ Đạo
 *   /admin/content/main-number/new      → Tổng quan / Nội dung / Số Chủ Đạo / Tạo mới
 */
import * as React from 'react'
import Link from 'next/link'
import { useRouter } from 'next/router'
import { ChevronRight } from 'lucide-react'

import { cn } from '@/lib/utils'
import { CONTENT_RESOURCES } from '@/lib/content-resources'
import { FLAT_NAV } from './admin-nav-config'

interface Crumb {
  label: string
  href?: string
}

export function AdminBreadcrumbs({ className }: { className?: string }) {
  const router = useRouter()
  const crumbs = React.useMemo<Crumb[]>(() => resolveCrumbs(router), [router.pathname, router.query])

  if (crumbs.length === 0) return null

  return (
    <nav aria-label="Breadcrumb" className={cn('flex items-center gap-1.5 text-sm text-muted-foreground', className)}>
      {crumbs.map((c, i) => {
        const last = i === crumbs.length - 1
        return (
          <React.Fragment key={i}>
            {i > 0 && <ChevronRight className="w-3.5 h-3.5 text-muted-foreground/60" />}
            {c.href && !last ? (
              <Link href={c.href} className="hover:text-foreground transition-colors">
                {c.label}
              </Link>
            ) : (
              <span className={cn(last && 'text-foreground font-medium')}>{c.label}</span>
            )}
          </React.Fragment>
        )
      })}
    </nav>
  )
}

function resolveCrumbs(router: ReturnType<typeof useRouter>): Crumb[] {
  const path = router.pathname
  const q = router.query

  // Root admin
  if (path === '/admin') return [{ label: 'Tổng quan' }]
  if (path === '/admin/login') return []

  const base: Crumb[] = [{ label: 'Tổng quan', href: '/admin' }]

  // Content resource pages
  if (path.startsWith('/admin/content/')) {
    const slug = q.resource as string | undefined
    const resource = CONTENT_RESOURCES.find((r) => r.slug === slug)
    const resLabel = resource?.label ?? slug ?? 'Nội dung'
    base.push({ label: 'Nội dung' })
    base.push({ label: resLabel, href: slug ? `/admin/content/${slug}` : undefined })
    if (path.endsWith('/new')) base.push({ label: 'Tạo mới' })
    else if (path.endsWith('/[id]')) base.push({ label: `#${q.id ?? ''}` })
    return base
  }

  // Other section
  const sectionMatches: Record<string, string> = {
    '/admin/news': 'Tin tức',
    '/admin/packages': 'Gói dịch vụ',
    '/admin/banks': 'Ngân hàng',
    '/admin/users': 'Người dùng',
    '/admin/payments': 'Thanh toán',
  }
  const section = Object.keys(sectionMatches).find((k) => path.startsWith(k))
  if (section) {
    base.push({ label: sectionMatches[section] ?? section, href: section })
    if (path.endsWith('/new')) base.push({ label: 'Tạo mới' })
    else if (path.endsWith('/[id]')) base.push({ label: `#${q.id ?? ''}` })
    return base
  }

  // Fallback — look up in FLAT_NAV
  const match = FLAT_NAV.find((n) => path.startsWith(n.href))
  if (match) base.push({ label: match.label })
  return base
}
