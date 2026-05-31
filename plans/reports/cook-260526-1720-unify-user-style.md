# Unify User-Side Style — Implementation Report

**Date:** 2026-05-26 17:20
**Goal:** Refactor user-facing pages to match home page style — friendly + smart.

## Home Design Tokens (extracted)
- Bg: `#031D2E` + gradient `linear-gradient(180deg, #031D2E 0%, #0A2A40 100%)` + warm orange/violet radial halos
- Primary: `#F96A2D` orange · Secondary: `#6F49FD` violet
- Fonts: Raleway (body), Philosopher (`var(--philosopher-font)`) for headings
- Buttons: rounded-pill 9999px (already global in MUI theme `light-theme-option.ts:71`)
- Cards: translucent `rgba(255,255,255,0.05)` + `1px solid rgba(255,255,255,0.10)` + backdrop-blur
- Motifs: orange accent bar (w:64 h:3 pill), glowing orange dot before headings, philosopher-numbered badges

## What Was Done

### Created (2 reusable primitives)
- `src/components/common/page-shell.tsx` — dark cosmic wrapper with hero heading + glass card; flag `bare` to drop the card
- `src/components/common/legal-document.tsx` — typography wrapper for legal pages (H2 orange accent bar, themed tables, orange links)

### Refactored to dark cosmic theme
- `pages/contact.tsx` — plain HTML → MUI glass cards, orange-themed inputs, info + form 2-col
- `pages/privacy.tsx`, `pages/terms.tsx`, `pages/refund-policy.tsx` — wrapped in PageShell + LegalDocument
- `pages/faq.tsx` — dark glass accordions (native `<details>`), orange "+" indicators, group glow-dot
- `pages/huong-dan.tsx` — vertical timeline with gradient number badges + orange dashed connector + CTA panel with multi-gradient
- `components/common/NotFound404.tsx` — cosmic bg + gradient "404" text + Philosopher heading; history-aware "Quay Lại"

### Polished light SaaS area (my-account, shop, checkout)
- `styles/admin.css` — `.account-shell` now has warm radial halos + Philosopher for h1/h2
- `components/my-account/account-layout.tsx` — added orange accent bar under H1, rounded-2xl sidebar
- `components/my-account/account-sidebar-nav.tsx` — stronger active state (border, shadow, semibold)
- `pages/my-account/index.tsx` — glow-dot before "Bắt đầu nhanh", rounded-2xl + hover lift on cards
- `pages/shop/index.tsx` — glow-dot + accent bar in catalogue header
- `pages/shop/[slug].tsx` — accent bar under title, gradient strip on summary card, glow-dot on H2
- `components/shop/product-card.tsx` — Philosopher product names, gradient header strip, larger hover lift
- `pages/check-out/[orderId].tsx` — accent bar + glow-dot on order summary, rounded-2xl

### Typecheck
- All edited files pass `tsc --noEmit` (pre-existing errors in unrelated files only)

## Design Decisions
- **Two visual worlds preserved on purpose:** static/marketing pages = dark navy + glass (matches home), my-account/shop = light SaaS dashboard with brand orange tokens — keeps form/data UX readable. Bridged via shared motifs (orange accent bar, glow dot, Philosopher headings, brand-orange primary).
- **Reusable wrappers** (`PageShell` + `LegalDocument`) eliminate duplicated cosmic-bg/glass-card code across 7+ pages. DRY.
- **No theme rewrite:** kept existing `light-theme-option.ts` and `admin.css` token system intact — only additive changes.

## Unresolved Questions
- Light vs dark for my-account/shop: left light (deliberate SaaS feel). User can request full dark conversion if preferred.
- `check-out/index.tsx` (legacy `/check-out` no orderId) still uses raw MUI Container without account-shell — likely dead code (real flow is `/check-out/[orderId]`). Left untouched. Confirm if it's still routed.
- `pages/ket-qua/index.tsx` and `pages/post/[id].tsx` not modified — they're heavy module-driven result/article pages already inheriting the dark theme. Worth a follow-up review if user wants tighter alignment.
