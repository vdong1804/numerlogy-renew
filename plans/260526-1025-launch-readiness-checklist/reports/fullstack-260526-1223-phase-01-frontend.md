# Phase 01 Frontend — Implementation Report

**Date:** 2026-05-26  
**Status:** Completed  
**Build:** PASS (clean, 0 errors)

---

## Files Created

| File | Purpose |
|---|---|
| `src/lib/consent-storage.ts` | localStorage nsq_consent_v1 get/set/clear, 365d expiry |
| `src/components/cookie-consent.tsx` | Banner: Chấp nhận / Từ chối / Tuỳ chỉnh, fires nsq_consent_updated event |
| `src/components/analytics.tsx` | GA4 + Meta Pixel injection gated by consent; trackPageView/SignUp/Checkout/Purchase helpers |
| `src/pages/terms.tsx` | Điều khoản sử dụng SSG — 10 sections, jurisdiction TP HCM |
| `src/pages/privacy.tsx` | Chính sách bảo mật SSG — NĐ 13/2023 compliant, data table, DPO contact |
| `src/pages/refund-policy.tsx` | Chính sách hoàn tiền SSG — 7-day/PDF-not-rendered condition |
| `src/pages/contact.tsx` | Liên hệ SSG — info block + form (alert only, no backend) |
| `next-sitemap.config.js` | Sitemap config, excludes admin/auth routes |
| `public/robots.txt` | Allow /, disallow admin/my-account/api/check-out |
| `public/manifest.json` | PWA manifest, theme #7c3aed |
| `sentry.client.config.ts` | Sentry browser skeleton, DSN from env, rate 0.1 |
| `sentry.server.config.ts` | Sentry server skeleton |
| `sentry.edge.config.ts` | Sentry edge skeleton |
| `docs/analytics-events.md` | Event taxonomy + consent flow + env vars |
| `docs/legal-content-sources.md` | Template versions + placeholder index |

## Files Modified

| File | Change |
|---|---|
| `src/layouts/Meta.tsx` | Added OG image, Twitter card, canonical auto-gen, JSON-LD prop, favicon links |
| `src/layouts/Footer.tsx` | LEGAL_LINKS const (4 real hrefs), copyright year dynamic, app version |
| `src/pages/_document.tsx` | Organization JSON-LD, favicon set links, manifest + theme-color |
| `src/pages/_app.tsx` | Mount `<Analytics />` + `<CookieConsent />` |
| `src/pages/admin/orders/[id].tsx` | Refund button (paid orders only) → Dialog with reason textarea → POST /admin/orders/{id}/refund |
| `src/lib/admin-dashboard-api.ts` | Added `refundOrder(id, reason)` typed wrapper |
| `package.json` | `postbuild: next-sitemap`, added next-sitemap + @sentry/nextjs@7 |

## Build Result

```
next build → compiled successfully, 90 static pages
postbuild  → next-sitemap generated sitemap-0.xml + sitemap.xml index
4 legal pages rendered as SSG (●): /terms /privacy /refund-policy /contact
```

## npm Install

- `next-sitemap` added
- `@sentry/nextjs@7` added (v8+ requires next ≥13.2, pinned to v7 for next@13.0.0)

## Skipped Items (user tasks)

| Item | Reason |
|---|---|
| Resend SPF/DKIM/DMARC DNS records | Requires DNS panel access — user action |
| Google Search Console TXT verify + sitemap submit | Requires GSC account — user action |
| Cloudflare Turnstile signup | Phase 03 scope |
| favicon.ico / apple-touch-icon.png / og-default.png | Binary assets — need design tool (spec: 180x180 PNG, 1200x630 PNG from numerology_favicon.svg) |
| Sentry DSN signup | User signs up free at sentry.io, sets SENTRY_DSN env var |
| Fill [BRACKETS] placeholders in legal pages | Awaiting business info (name, MST, address, email, phone) |
| Submit sitemap to GSC | After DNS + GSC verify complete |
| trackPageView router integration | Phase 03 (after CSP tuning) |

## Unresolved Questions

1. `NEXT_PUBLIC_SITE_URL` env var not in `.env` — Meta.tsx canonical and sitemap will fall back to `https://nhansinhquan.vn`; confirm this is the production domain.
2. `NEXT_PUBLIC_APP_VERSION` env var optional — footer shows `v3` fallback from package.json version.
3. Sentry `@sentry/nextjs@7` installed (not v8) due to `next@13.0.0` peer constraint — upgrade next to ≥13.2 to unlock Sentry v8 features.
4. `trackPageView()` not yet wired to `router.events` — deferred to Phase 03 to avoid conflicts with CSP tuning.
