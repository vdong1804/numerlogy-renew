# Phase 04 Frontend — Implementation Report

**Date:** 2026-05-26  
**Status:** completed

---

## Files Modified

| File | Change |
|------|--------|
| `src/lib/admin-dashboard-api.ts` | +50 lines: `OrderSearchFilters` interface, `searchOrders()`, `exportOrdersCsv()` |
| `src/pages/admin/orders/index.tsx` | Rewritten (175 lines): search form, CSV export, empty state, pagination via `searchOrders` |
| `src/modules/home/TeacherInfo.tsx` | `<img>` → `next/image` (bg-teacher.png 627KB); improved alt |
| `src/modules/home/Banner.tsx` | `animated.img` → `animated.div` + `next/image` (adalash_banner.png 317KB); fixed zodiac alt |
| `src/modules/home/LookUpNumerology.tsx` | Fixed empty alt on satellite.png |

## Files Created

| File | Purpose |
|------|---------|
| `src/components/admin/order-search-form.tsx` | Search form sub-component (110 lines) — extracted from orders page to keep index.tsx ≤200 LOC |
| `src/lib/image-audit.md` | Full audit: 10 `<img>` tags, status per file, deferred actions |

---

## Admin Orders UI

- Search fields: Email, Mã đơn (ref_code), Trạng thái (select: tất cả/pending/paid/refunded/expired/cancelled), Từ ngày, Đến ngày
- Enter key triggers search; "Xóa lọc" resets all fields to empty
- "Xuất CSV" button (DownloadIcon) calls `exportOrdersCsv(activeFilters)` → blob download `orders-YYYYMMDD.csv`
- Empty state (InboxIcon) shown when 0 results
- Pagination preserved via `page` field in filters object

## Image Audit Findings

- Total `<img>` tags in src/: **10**
- Missing alt before fix: **3** (zodiac.png, satellite.png, adalash_banner.png had `alt=""` or vague "Banner image")
- Alt fixed: **3**
- Migrated to `next/image`: **2** (bg-teacher.png 627KB, adalash_banner.png 317KB)
- Remaining `<img>` deferred: **6** (SVG logos in Header/Footer/auth-shell, QR display, flag CDN icons)
- Large images still as CSS backgrounds (not `<img>`): 4 files totaling ~5.6MB — addressable only via Cloudflare Polish or manual WebP conversion, documented in audit

## Build Result

**PASS** — 94 pages compiled, 0 errors, sitemap generated.  
`/admin/orders` bundle: 3.85kB page + 198kB first load JS (no regression).

---

## Skipped (User/Ops Tasks)

- Blog content (5-10 bài): via admin News CRUD
- Cloudflare DNS/proxy setup: registrar panel change
- Mobile QA real device
- Lighthouse re-audit (manual)
- Final E2E smoke test
- Admin lint cleanup sprint (deferred per next.config.js note)
- Replace huong-dan placeholder images with real screenshots (needs design assets)

---

## Unresolved Questions

1. Backend `/admin/orders` query params — does it support `email`, `ref_code`, `date_from`, `date_to` filters yet, or only `status`/`limit`/`offset`? Frontend `searchOrders()` sends them; backend agent must extend the router (Phase 04 Day 1 step 1-2).
2. `/admin/orders/export.csv` endpoint — not yet confirmed created by backend agent. `exportOrdersCsv()` is wired up and will throw a readable error until endpoint is live.
3. `adalash_thanh2.png` (527KB) — not found in any active `<img>` tag; may be unused. Confirm then delete to reduce bundle.
4. `reader_comment.png` (611KB) — used location unclear from grep (possibly CSS background or dynamic import). Confirm before migrating.
