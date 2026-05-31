---
name: launch-readiness-checklist
status: implemented
created: 2026-05-26
target_completion: 2026-06-23
total_phases: 4
estimated_duration: 4 weeks
phase_01_status: implemented
phase_02_status: implemented
phase_03_status: implemented
phase_04_status: implemented
last_synced: 2026-05-26
implemented_on: 2026-05-26
---

# Plan — Launch Readiness Checklist

## Overview

Đưa Numerology platform từ "v1.1 code complete" lên trạng thái public launch (chạy marketing). Plan 4 tuần, free tier SaaS, giải quyết 3 risk chính: payment/fulfillment, observability, pháp lý+SEO.

**Brainstorm:** [../reports/brainstorm-260526-1025-launch-readiness-checklist.md](../reports/brainstorm-260526-1025-launch-readiness-checklist.md)

## Locked Decisions

- Email verification NOT bật (giữ nguyên, bù bằng Cloudflare Turnstile CAPTCHA)
- Stay free tier: Sentry / Resend / UptimeRobot / Cloudflare
- Refund minimal: admin button manual, no formal state machine
- Reconcile-SePay cron: 15 phút interval, pull window 24h
- Cookie consent gate analytics (GA4 + Pixel chỉ fire sau consent)
- CSP relaxed (allow inline cho GA/Pixel) — siết về strict post-launch
- Turnstile (Cloudflare free unlimited) thay vì hCaptcha

## Phases

| # | Phase | File | Tuần | Status |
|---|-------|------|------|--------|
| 01 | Pháp lý + SEO foundation + Analytics | [phase-01-legal-seo-analytics.md](./phase-01-legal-seo-analytics.md) | Tuần 1 | implemented |
| 02 | Payment safety + Observability | [phase-02-payment-safety-observability.md](./phase-02-payment-safety-observability.md) | Tuần 2 | implemented |
| 03 | Security + UX polish + Email deliverability | [phase-03-security-ux-email.md](./phase-03-security-ux-email.md) | Tuần 3 | implemented |
| 04 | Content/SEO + Buffer + Go-live | [phase-04-content-seo-golive.md](./phase-04-content-seo-golive.md) | Tuần 4 | implemented |

## Dependencies

```
01 (legal+SEO+analytics) ─┐
                          ├─→ 03 (security+UX+email) ─→ 04 (content+go-live)
02 (payment+observ)     ──┘
```

Phase 01 + 02 chạy song song được (khác stack). Phase 03 cần cả 2. Phase 04 = polish + go-live.

## External Dependencies (user trách nhiệm)

- DNS access `nhansinhquan.vn` (Resend SPF/DKIM/DMARC, GSC TXT, Cloudflare nameserver) — **làm ngày 1 vì propagate 24-48h**
- Thông tin DN cho Contact page (tên/địa chỉ/MST/GPKD)
- Sentry / UptimeRobot / Cloudflare / GA4 / Meta Business signup (free)
- Bank account cho SePay (đã có per v1.1)
- Nội dung Terms/Privacy/Refund — dùng template + customize, luật sư review nếu kỹ

## Pending Decisions (xử lý khi tới)

| Q | Default | Override khi |
|---|---------|--------------|
| Email order-paid PDF attach vs link | Link (auth-protected) | User báo deliverability vấn đề |
| Cloudflare proxy vs DNS-only | Proxy (CDN + DDoS) | Backend cần real client IP cho rate limit |
| Soft launch trước public | Có, 1 tuần beta nhỏ | User muốn launch ngay |

## Implementation Notes (2026-05-26)

**All 4 phases code-able subset implemented (concurrent 2026-05-26 session).**

**Phase 04 — Admin Ops + SEO + Image Audit + Go-live Runbooks.**

- Backend: `csv_export_service` (UTF-8 BOM Excel VN, 10k row limit); `/admin/orders` extended query params (email/ref_code/status/date_from/date_to/page/page_size); `GET /admin/orders/export.csv` StreamingResponse superuser-only; `go-live-runbook.md` (5 sections, 12 deploy steps, rollback); `post-launch-monitoring.md` (daily/weekly checks, alert thresholds).
- Frontend: `searchOrders` + `exportOrdersCsv` typed API; admin/orders/index.tsx rewritten (175 LOC, 5-input search form + CSV export button + empty state + pagination); order-search-form.tsx extracted (110 LOC); `image-audit.md` doc (10 img tags, 3 alt fixes, 2 next/image migrations for bg-teacher 627KB + adalash_banner 317KB).
- Code review 7.5/10: fixed 1 critical (http_http_status typo → NameError → 500) + 5 high (SQL ILIKE wildcard escape + max_length, CSV formula injection prevention via `_safe_csv_cell`, DatePicker Bangkok TZ contract via `toIsoWithBangkokTz`, CSV row limit doc, exportOrdersCsv JSON error UX).
- Test: 173/190 pass (17 pre-existing fails unchanged, 0 regressions).
- **Skipped (user actions):** 5-10 blog content via admin News CRUD; Cloudflare DNS + proxy + CDN setup; soft launch beta invite 50-100 user; mobile QA real device; final smoke E2E; ads enable + 24h monitor go-live; admin lint cleanup sprint (deferred backlog).

**Phase 01 + 02 shipped in parallel (same 26-hour session).**

- Frontend: 12 files created, 7 files modified. Build passed, sitemap generated, 90 pages indexed. Legal pages SSG, cookie consent + analytics gate working.
- Backend: 8 files created, 11 files modified. Migration 0008 valid, reconcile cron 15min registered, refund endpoint + signed download tokens implemented. 175/191 tests pass (15 pre-existing fails, unrelated to Phase 01+02).
- Code review score 8.7/10: 3 critical + 6 high fixes applied (Sentry DSN env rename, PII scrubber, path traversal guard, datetime.utcnow → utc-aware, commit per-order, idempotency check broadened, token type field, URL builder fix, refund note logic).
- **Skipped items (user action required):**
  - DNS: Resend SPF/DKIM/DMARC + GSC TXT setup (24-48h propagate)
  - Sentry/UptimeRobot/Cloudflare: free account signup + DSN/monitor creation
  - Binary assets: favicon.ico, apple-touch-icon.png, og-default.png (need design tool)
  - E2E real payment: bank app interaction
  - Backup restore staging: requires infra/Docker
  - Legal page placeholders: awaiting business info (name, MST, address, email, phone)

**Phase 03 shipped (2026-05-26).**

- Backend (Day 1–4): slowapi rate limit (login 5/min, register 3/min, forgot-password 3/min IP+email, webhook 100/min) + Turnstile verify service + nginx security headers (HSTS 2y + 4 headers + CSP relaxed for GA/Pixel) + email plain-text fallback (6 .txt pairs) + base.html Jinja unsubscribe footer + email_outbox multipart dispatch.
- Frontend (Day 1–4): Turnstile widget (dev fallback token + prod guard) + register/forgot-password integration + FAQ 15 Q&A (3 groups: Mua hàng/Thanh toán/Báo cáo) + Hướng dẫn 5-step guide + empty-state component + 3 skeleton components (order/report/shop) + my-account orders/reports empty states + Footer FAQ/Hướng dẫn links + next.config.js OAuth env cleanup + NEXT_PUBLIC_TURNSTILE_SITE_KEY.
- Code review 8.9/10: fixed 2 critical (CSP connect-src wrong host + ignoreBuildErrors comment) + 5 high (Turnstile prod guard, dev-skip block, XFF spoof via TRUSTED_PROXY_MODE, rate limit per-worker doc, _forgot_password_key async body parse).
- Test: 173/190 pass (17 pre-existing failures unrelated to Phase 03, admin endpoints).
- **Skipped items (user action/external):**
  - Cloudflare Turnstile site signup (need site key + secret from dashboard)
  - DNS Resend verify (Phase 01 setup, test in Phase 04)
  - Mobile QA real device iOS + Android (defer Phase 04 as full sprint)
  - mail-tester.com submission (user runs before prod deploy)
  - SSL Labs A+ scan (deferred, HSTS age validation post-launch)
  - Admin lint cleanup (100+ pre-existing errors, create Phase 04 backlog task)

## Success Criteria (30d post-launch)

- ≥95% orders auto-fulfill <30s
- 0 case user trả tiền không nhận hàng
- Sentry error rate <0.5%
- Uptime ≥99.5%
- Lighthouse mobile ≥85
- FB/Google Ads duyệt lần đầu
- Email open ≥30%, bounce <2%
