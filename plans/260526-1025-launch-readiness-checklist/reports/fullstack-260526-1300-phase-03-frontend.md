# Phase 03 Frontend — Implementation Report

## Files Created
- `src/components/turnstile-widget.tsx` — Cloudflare Turnstile widget, dev fallback when no site key
- `src/components/empty-state.tsx` — Generic MUI empty state (icon + title + desc + CTA)
- `src/components/skeleton/order-card-skeleton.tsx` — Tailwind animate-pulse row skeleton
- `src/components/skeleton/report-card-skeleton.tsx` — Tailwind animate-pulse card skeleton
- `src/components/skeleton/shop-item-skeleton.tsx` — Tailwind animate-pulse product card skeleton
- `src/pages/faq.tsx` — 15 Q&A, 3 groups, native `<details>` accordion, SSG
- `src/pages/huong-dan.tsx` — 5-step guide, placeholder image divs, CTA, SSG

## Files Modified
- `src/pages/register.tsx` — added TurnstileWidget, captchaToken state, disabled submit when !captchaToken, captcha_token in API body
- `src/pages/forgot-password.tsx` — same pattern as register
- `src/pages/my-account/orders/index.tsx` — replaced bare `<Skeleton>` with OrderCardSkeleton x3, replaced plain text empty state with EmptyState component (ShoppingBagOutlined icon, CTA → /shop)
- `src/pages/my-account/reports/index.tsx` — replaced `<Skeleton>` with ReportCardSkeleton x4, replaced plain text empty state with EmptyState (DescriptionOutlined icon, CTA → /shop)
- `src/layouts/Footer.tsx` — prepended FAQ + Hướng dẫn sử dụng to LEGAL_LINKS
- `next.config.js` — removed OAuth env vars (NEXTAUTH_*, GOOGLE_*, FACEBOOK_*, TWITTER_*, DJANGO_AUTH_*), added NEXT_PUBLIC_TURNSTILE_SITE_KEY; ignore flags kept (see below)
- `.env.example` — added NEXT_PUBLIC_TURNSTILE_SITE_KEY with comment

## Turnstile Integration
- Widget loads `api.js` async on mount, registers global callback, renders explicit widget
- Dev fallback: empty site key → calls onSuccess('dev-skip-token') after 100ms, shows [CAPTCHA disabled — dev mode] placeholder
- Both register + forgot-password: submit button disabled while captchaToken === '' (no captcha bypass in prod)
- captcha_token included in POST body for backend verification

## FAQ + Hướng dẫn
- `/faq`: 15 Q&A, groups: Mua hàng (5) / Thanh toán (5) / Báo cáo (5), native `<details>` accordion, SSG, Meta/OG tags
- `/huong-dan`: 5 steps with numbered badge, title, description, placeholder image div; CTA Đăng ký + Cửa hàng; SSG
- Both linked in Footer LEGAL_LINKS, accessible without login

## next.config.js Changes
- Before: ignoreBuildErrors: true, ignoreDuringBuilds: true, 9 OAuth env vars
- After: same ignore flags (kept — see below), OAuth vars removed, NEXT_PUBLIC_TURNSTILE_SITE_KEY added

## Build Result
- Build PASS: 94 pages, 0 errors
- `/faq` and `/huong-dan` compiled as static (SSG)
- ignore flags KEPT: removing them reveals 100+ pre-existing prettier/eslint errors in admin components (formatting, import-sort, no-nested-ternary). These are pre-existing, not introduced by this phase. Flagged HIGH priority for dedicated cleanup pass.

## Skipped (user tasks / out of scope)
- Cloudflare Turnstile dashboard signup + actual site key + secret key
- Backend captcha verification (backend agent scope)
- Mobile QA real device iOS + Android
- Lighthouse mobile audit
- Toast lib refactor: admin pages use `sonner` via `@/components/admin/admin-toast` consistently; public pages use MUI Alert/native — no sonner on public side. Pattern is consistent within each domain, no unification needed this phase.

## Unresolved Questions
1. NEXT_PUBLIC_TURNSTILE_SITE_KEY: needs actual value from Cloudflare dashboard before prod deploy — user action required.
2. Turnstile secret key: backend must set TURNSTILE_SECRET_KEY env var for server-side token verification.
3. Placeholder images in /huong-dan: replace "Ảnh minh họa" divs with real screenshots before launch.
4. Pre-existing admin lint errors (~100+): need dedicated cleanup sprint to safely remove ignoreDuringBuilds + ignoreBuildErrors flags.
