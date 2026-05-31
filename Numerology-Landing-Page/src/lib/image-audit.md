# Image Audit — Phase 04

Generated: 2026-05-26

## Summary

| Metric | Count |
|--------|-------|
| Total `<img>` tags found (src/) | 10 |
| Missing `alt` (before fix) | 3 |
| Fixed in this phase | 3 |
| Migrated to `next/image` | 2 |
| Remaining `<img>` (deferred) | 6 |

---

## All `<img>` Occurrences

| File | Line | Src | Alt status | Action taken |
|------|------|-----|-----------|--------------|
| `src/layouts/Header.tsx` | 121 | `/numerology_logo.svg` | `alt="Logo Numerology"` | Keep `<img>` — SVG logo, tiny, no LCP impact |
| `src/layouts/Header.tsx` | 296 | `/numerology_favicon.svg` | `alt="Logo Numerology"` | Keep `<img>` — mobile drawer, SVG, fine |
| `src/layouts/Footer.tsx` | 65 | `/numerology_logo.svg` | `alt="Logo"` | Minor: alt could be more descriptive. Defer — not LCP |
| `src/components/form/SearchNumerologyForm.tsx` | 213 | `flagcdn.com/w20/{code}.png` | `alt=""` (intentional) | Keep — flag icons, decorative, empty alt correct |
| `src/components/checkout/qr-display.tsx` | 32 | `{qrUrl}` | `alt="QR {refCode}"` | Keep `<img>` — dynamic QR URL, next/image won't cache external URLs correctly |
| `src/components/auth/auth-shell.tsx` | 59 | `/numerology_logo.svg` | `alt="Numerology"` | Keep `<img>` — auth page logo, SVG |
| `src/modules/home/TeacherInfo.tsx` | 97 | `/assets/images/bg-teacher.png` (627KB) | `alt="Teacher"` | **MIGRATED** to `next/image` with descriptive alt |
| `src/modules/home/LookUpNumerology.tsx` | 28 | `/assets/images/satellite.png` (104KB) | `alt=""` (missing) | **FIXED alt** — added descriptive Vietnamese text |
| `src/modules/home/Banner.tsx` | 197 | `/assets/images/adalash_banner.png` (317KB) | `alt="Banner image"` | **MIGRATED** to `next/image` inside `animated.div`; improved alt |
| `src/modules/home/Banner.tsx` | 221 | `/assets/images/zodiac.png` (113KB) | `alt=""` (missing) | **FIXED alt** — added descriptive Vietnamese text |

---

## Large Images (≥100KB) — next/image Migration Status

| Image | Size | Status | Notes |
|-------|------|--------|-------|
| `numerology_info_bg.png` | 1864KB | Deferred | Used as CSS `background-image` in Tailwind/MUI `sx`, not `<img>` tag |
| `teacher_info_bg.png` | 1805KB | Deferred | CSS background, not `<img>` tag |
| `banner-search-result.png` | 1656KB | Deferred | CSS background in shop/ket-qua page |
| `sky-bg.png` | 1059KB | Deferred | CSS background |
| `bg-teacher.png` | 627KB | **MIGRATED** | `next/image` with `priority`, 600x700 |
| `reader_comment.png` | 611KB | Deferred | Check if used as `<img>` or background |
| `adalash_thanh2.png` | 527KB | Deferred | Not found in active `<img>` tags |
| `banner-article.png` | 516KB | Deferred | Used in post/blog pages — defer to content sprint |
| `bg-blog-numberology.png` | 416KB | Deferred | CSS background |
| `adalash_banner.png` | 317KB | **MIGRATED** | `next/image` inside `animated.div` wrapper; `priority` |
| `zodiac.png` | 113KB | Fixed alt only | Decorative absolute-positioned element; `next/image` requires static dimensions — defer full migration |
| `satellite.png` | 104KB | Fixed alt only | Decorative; same reason as zodiac |

---

## Deferred Actions (Recommended Follow-up)

1. **CSS background images** (`numerology_info_bg.png` 1.9MB, `sky-bg.png` 1MB etc.) — convert to WebP via `sharp` or Cloudflare Polish. Not addressable via `next/image`.
2. **`reader_comment.png`** (611KB) — confirm usage location then migrate if rendered as `<img>`.
3. **`banner-article.png`** (516KB) — used in `/post/[id]` blog thumbnail. Migrate during blog content sprint.
4. **`Footer.tsx` logo alt** — change `alt="Logo"` to `alt="Logo Thần Số Học"` (minor a11y polish).
5. **Absolute-positioned decorative images** (`zodiac.png`, `satellite.png`) — migrate to `next/image` once designers confirm final dimensions (avoid layout shift).
6. **`adalash_thanh2.png`** (527KB) — grep shows not in active `<img>` tags; may be unused. Run `grep -r adalash_thanh2` to confirm before deleting.

---

## Remaining `<img>` Tags (Not Owned by This Phase)

- `src/layouts/Footer.tsx` — minor (logo, tiny SVG)
- `src/components/checkout/qr-display.tsx` — functional, keep as `<img>`
- `src/components/auth/auth-shell.tsx` — auth page logo, low priority
- `src/components/form/SearchNumerologyForm.tsx` — flag CDN icons, empty alt intentional
