# Launch Readiness Checklist — Numerology Platform

**Date:** 2026-05-26
**Context:** Public launch (chạy marketing), 2-4 tuần, free tier SaaS
**Top concerns:** Payment & fulfillment | Stability & observability | Pháp lý & SEO/marketing
**Current state:** v1.1 implemented (shop/orders/SePay/my-account/email outbox/APScheduler)

---

## 1. Problem Statement

Platform code complete nhưng chưa launch-ready do thiếu các lớp **pháp lý**, **SEO/marketing**, **observability**, **payment safety net**. Risk chính khi go-live:
- Bị FB/Google Ads từ chối duyệt (thiếu Privacy/Terms/Contact)
- Lỗi prod im lặng (no Sentry)
- User trả tiền không nhận hàng (webhook miss, no reconcile cron, no refund flow)
- Brute-force/spam (no rate limit, no CAPTCHA)
- Không index Google (no sitemap, no OG)
- Không đo được ad spend (no GA4/Pixel)

---

## 2. Approach Evaluated

**A. Big-bang full hardening (8+ tuần)** — All-in Sentry + Prometheus + Redis + CI/CD + audit log + refund formal + E2E.
✗ Trượt timeline 2-4 tuần. Over-engineer cho launch nhỏ.

**B. Minimal must-have only (1 tuần)** — Chỉ legal + analytics + Sentry.
✗ Bỏ qua reconcile-SePay = risk chính của user. Không có rate limit khi chạy ads = lộ brute-force.

**C. ✅ Tiered P0/P1/P2 checklist (2-4 tuần, free tier)** — Khoá tất cả launch-blocker P0, làm P1 khi kịp, defer P2 post-launch.
✓ Vừa timeline, vừa giải quyết 3 concern, vừa stay free tier.

**Quyết định: Approach C.**

---

## 3. P0 — MUST trước go-live (block launch nếu thiếu)

### 3.1 Pháp lý (concern: legal/SEO) — 3-5 ngày

- [ ] **Terms of Service** (Điều khoản sử dụng) — page `/terms`
- [ ] **Privacy Policy** (Chính sách bảo mật) — page `/privacy`, tuân NĐ 13/2023 về bảo vệ dữ liệu cá nhân VN
- [ ] **Refund Policy** (Chính sách hoàn tiền) — page `/refund-policy`, bắt buộc cho ecom VN
- [ ] **Contact page** + thông tin DN (tên, địa chỉ, MST/GPKD nếu có, hotline, email) — bắt buộc duyệt FB/Google Ads
- [ ] **Cookie consent banner** (chấp nhận/từ chối optional analytics) — block GA4/Pixel firing đến khi consent
- [ ] Footer link tới tất cả 4 page trên + version + copyright

**Files:** `src/pages/terms.tsx`, `src/pages/privacy.tsx`, `src/pages/refund-policy.tsx`, `src/pages/contact.tsx`, `src/components/cookie-consent.tsx`, `src/layouts/Main.tsx` (footer)

---

### 3.2 SEO foundation (concern: SEO) — 2 ngày

- [ ] `robots.txt` (allow public, disallow `/admin`, `/my-account`, `/api`)
- [ ] `sitemap.xml` auto-generate qua `next-sitemap` (free package) — include `/`, `/shop`, `/shop/[slug]`, `/post/[id]`
- [ ] OG/Twitter meta động per page (title, description, image 1200x630) — sửa `src/layouts/Meta.tsx`
- [ ] Favicon set đầy đủ: `favicon.ico`, `apple-touch-icon.png`, `manifest.json`, `safari-pinned-tab.svg`
- [ ] Canonical URL tag (tránh duplicate content)
- [ ] JSON-LD structured data: `Organization` (homepage), `Product` (shop detail), `Article` (blog)
- [ ] `next.config.js`: thêm `images.domains` cho ảnh external + bật `images.formats: ['image/avif','image/webp']`
- [ ] Page-specific `<title>` + meta description (không dùng "Thần số học" generic everywhere)

**Files:** `public/robots.txt`, `next-sitemap.config.js`, `src/layouts/Meta.tsx`, `public/manifest.json`, page components

---

### 3.3 Analytics & marketing pixel (concern: SEO) — 1 ngày

- [ ] **Google Analytics 4** — gtag script + consent gate (sau cookie consent)
- [ ] **Meta Pixel** — `fbq('init')` + `fbq('track', 'PageView')` + standard events (`InitiateCheckout`, `Purchase`)
- [ ] **Google Search Console** verify domain (TXT DNS) + submit sitemap
- [ ] **Microsoft Clarity** (free, UX heatmap) — optional, debug UX nhanh
- [ ] Event taxonomy doc (`docs/analytics-events.md`): `sign_up`, `view_shop`, `add_to_cart`, `purchase`, `view_report`

**Files:** `src/components/analytics.tsx`, `src/pages/_app.tsx`, `docs/analytics-events.md`

---

### 3.4 Payment & fulfillment safety net (concern: payment) — 3-4 ngày

- [ ] **Reconcile-SePay cron** — APScheduler job mỗi 15 phút: pull SePay transactions list, match với orders `pending`, fulfill nếu webhook miss. **CRITICAL.**
- [ ] **Refund tối thiểu (manual)** — admin button "Hoàn tiền": gán lại quota / disable user_report + ghi note vào `orders.admin_notes` (column mới). Không cần workflow tự động.
- [ ] **"Liên hệ hỗ trợ" CTA** trên `/check-out/[orderId]` khi pending >5 phút (hiển thị Zalo/email admin)
- [ ] **E2E test thật** trước go-live: 1 transaction 10k real → verify auto-fulfill → check email → download PDF
- [ ] **Email order-paid** có link tải PDF trực tiếp (không bắt login lại)
- [ ] **Backup restore test** — chạy 1 lần `pg_restore` lên DB staging, verify data toàn vẹn

**Files:** `app/jobs/reconcile_sepay.py`, `app/services/sepay_service.py` (add `list_recent_transactions`), `app/routers/admin/orders.py` (add refund endpoint), `alembic/versions/0008_orders_admin_notes.py`, `src/pages/check-out/[orderId].tsx`

---

### 3.5 Observability (concern: stability) — 1-2 ngày

- [ ] **Sentry FastAPI** — free tier 5k events/mo + 1 user. `sentry-sdk[fastapi]`. Capture unhandled, traceback, slow endpoints.
- [ ] **Sentry Next.js** — `@sentry/nextjs` wizard, source maps upload
- [ ] **UptimeRobot** ping `/health/detail` mỗi 5 phút, alert email khi down
- [ ] Verify `/health/detail` endpoint trả DB status + email provider status (đã có per changelog v1.1)
- [ ] Structured logging review: ensure `logger.error` calls include context (user_id, order_id)
- [ ] Sentry env tag: `production` vs `staging` (tránh nhiễu trong dashboard)

**Files:** `app/main.py` (sentry init), `numerology-api/pyproject.toml`, `Numerology-Landing-Page/sentry.*.config.ts`

---

### 3.6 Security baseline (concern: payment/sec) — 1-2 ngày

- [ ] **Rate limit** `/auth/login` (5/min/IP), `/auth/register` (3/min/IP), `/auth/forgot-password` (3/min/IP+email), `/api/webhooks/sepay` (100/min/IP). Dùng `slowapi` in-memory (no Redis cần).
- [ ] **Nginx security headers** — thêm vào `deploy/nginx.conf`:
  ```
  add_header Strict-Transport-Security "max-age=63072000; includeSubDomains" always;
  add_header X-Frame-Options "SAMEORIGIN" always;
  add_header X-Content-Type-Options "nosniff" always;
  add_header Referrer-Policy "strict-origin-when-cross-origin" always;
  add_header Permissions-Policy "geolocation=(), microphone=(), camera=()" always;
  ```
- [ ] **CSP basic** — `default-src 'self'; img-src 'self' data: https:; script-src 'self' 'unsafe-inline' https://www.googletagmanager.com https://connect.facebook.net;` (test kỹ vì có thể block GA/Pixel inline)
- [ ] **Sửa `next.config.js`**: bỏ `ignoreBuildErrors: true` + `ignoreDuringBuilds: true` (CI catch type/lint errors), dọn env vars OAuth cũ (Google/Facebook/Twitter/Django) không dùng nữa
- [ ] **Cloudflare Turnstile** CAPTCHA (free unlimited) trên `/register` + `/forgot-password` — chống bot khi chạy ads
- [ ] Verify CORS origins prod chỉ allow `https://nhansinhquan.vn` (không wildcard)
- [ ] Verify JWT secret prod ≥32 chars random, không commit vào repo

**Files:** `app/main.py` (slowapi), `app/routers/auth.py` (decorators), `deploy/nginx.conf`, `Numerology-Landing-Page/next.config.js`, `src/pages/register.tsx` (Turnstile)

---

## 4. P1 — SHOULD nếu kịp trong 2-4 tuần

### 4.1 UX & content — 3-5 ngày

- [ ] **FAQ page** `/faq` — 10-15 câu phổ biến (cách mua, thanh toán bao lâu, hoàn tiền, đổi gói…). Giảm 30-50% support load.
- [ ] **Hướng dẫn sử dụng** `/huong-dan` — visual step-by-step mua + xem báo cáo
- [ ] **Mobile QA** real device — iOS Safari + Android Chrome, test full flow: register → mua → checkout → nhận email → download
- [ ] **Loading states / skeleton** thay vì spinner blank
- [ ] **Empty states**: my-account/orders khi 0 orders, my-account/reports khi 0 reports
- [ ] **Toast standardize** (success/error/warning) — verify hiện đang dùng gì
- [ ] **Hero CTA optimize** — clear value prop + social proof (số user đã mua, testimonial)

### 4.2 Email deliverability — 1 ngày

- [ ] Verify Resend SPF + DKIM + DMARC records cho `nhansinhquan.vn` (DNS propagate 24-48h — làm sớm)
- [ ] Test gửi tới Gmail/Outlook/Yahoo: vào Inbox, không Spam
- [ ] Plain-text fallback cho mọi HTML email template
- [ ] Unsubscribe link footer (CAN-SPAM compliance) — link tới `/my-account/settings`

### 4.3 Admin ops — 2 ngày

- [ ] **Export orders CSV** (filter date range) — kế toán cuối tháng
- [ ] **Search/filter orders** nâng cao: theo email user, ref_code, status, date range
- [ ] **Daily revenue summary** verify đã có trong dashboard
- [ ] **Mark-as-paid bulk** (nếu admin nhận nhiều tx offline)

### 4.4 SEO content & perf — 3-5 ngày

- [ ] **5-10 bài blog** chất lượng (đã có News CRUD) — long-tail keyword: "số chủ đạo là gì", "ý nghĩa số 8 thần số học"…
- [ ] **Internal linking** giữa news → shop product (CTA)
- [ ] **Image alt text** mọi `<img>` (a11y + SEO)
- [ ] **Lighthouse audit** — target ≥85 mobile (perf + a11y + SEO + best practices). Fix Core Web Vitals.
- [ ] **`next/image` audit** — thay `<img>` → `Image` cho ảnh ≥100KB
- [ ] **Cloudflare CDN** (free) — DNS proxy + cache tĩnh + DDoS protect basic

---

## 5. P2 — POST-launch (defer)

- [ ] Redis cache numerology content (khi >1k req/min)
- [ ] CI/CD GitHub Actions (test + build PR)
- [ ] Audit log admin mutations (khi đa-admin)
- [ ] Playwright E2E critical paths
- [ ] k6 load test webhook + checkout
- [ ] 2FA admin
- [ ] Refund workflow formal (state machine, partial refund)
- [ ] Reconcile audit dashboard
- [ ] Prometheus + Grafana
- [ ] Multi-language (i18n đã setup, chưa dùng)

---

## 6. Lịch suggest (2-4 tuần)

| Tuần | Focus | Items |
|------|-------|-------|
| **1** | Pháp lý + SEO foundation | 3.1, 3.2, 3.3 + DNS Resend (chạy DNS sớm vì 24-48h) |
| **2** | Payment safety + Observability | 3.4, 3.5 + E2E test thật |
| **3** | Security + UX polish | 3.6, 4.1, 4.2 |
| **4** | Content/SEO + buffer + go-live | 4.3, 4.4, soft launch internal, fix lastminute |

---

## 7. Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Reconcile cron miss tx → user complaint | Medium | High | Pull window 24h, log mọi mismatch, alert Sentry |
| Sentry free tier 5k events tràn → mù lỗi | Medium | Med | Filter noise (4xx ignored), upgrade khi >2k user |
| CSP break GA/Pixel | High khi deploy | Med | Test trên staging 1 ngày trước prod |
| FB Ads từ chối duyệt (thiếu thông tin DN) | High nếu thiếu | High | Hoàn thiện Contact + Privacy trước khi submit |
| DNS propagate Resend chậm → email vào Spam | Medium | High | Setup DNS tuần 1, test tuần 2 |
| Backup restore fail | Low | Critical | Test 1 lần lên staging trước launch |

---

## 8. Success Metrics (30 ngày post-launch)

- ✅ ≥95% orders auto-fulfill <30s
- ✅ 0 case user trả tiền không nhận hàng (reconcile cron bắt được mọi miss)
- ✅ Sentry error rate <0.5% requests
- ✅ Uptime ≥99.5%
- ✅ Lighthouse mobile ≥85
- ✅ Google index ≥80% sitemap URLs trong 14 ngày
- ✅ FB Ads + Google Ads duyệt thành công ngay lần submit đầu
- ✅ Email open rate ≥30% (order-paid), bounce <2%

---

## 9. Dependencies & External

- DNS access cho `nhansinhquan.vn` (Resend SPF/DKIM/DMARC, GSC TXT verify, Cloudflare nameserver)
- Sentry account (free signup)
- UptimeRobot account (free signup)
- Cloudflare account (free signup, Turnstile + CDN)
- GA4 property + Meta Business Manager (đã có?)
- Thông tin DN cho Contact page (tên/địa chỉ/MST nếu có)
- Nội dung Terms/Privacy/Refund — luật sư review hoặc dùng generator + customize

---

## 10. Out of Scope (Brainstorm này không bao gồm)

- Mobile app (Q3+)
- Multi-tenancy (2027+)
- Real-time WebSocket
- Email verification on register (user chọn không bật — chấp nhận risk fake email, bù bằng CAPTCHA)

---

## Unresolved Questions

1. **Thông tin DN** cho Contact page — đã có MST/GPKD chưa? Nếu chưa, dùng cá nhân hay đăng ký HKD?
2. **Refund policy** — chính sách thực tế: hoàn 100% trong X ngày? Có điều kiện gì?
3. **Email order-paid** — đính kèm PDF trực tiếp hay chỉ link tải (link an toàn hơn nhưng cần auth)?
4. **Cloudflare proxy** — chấp nhận để Cloudflare nhìn traffic (DDoS + cache) hay chỉ DNS-only?
5. **Turnstile vs hCaptcha** — Turnstile UX tốt hơn nhưng dùng Cloudflare; hCaptcha độc lập.
6. **CSP**: strict (block inline script) hay relaxed (allow GA/Pixel inline)? Strict = secure hơn, cần nonce config.
7. **Soft launch trước public**: muốn mời nhóm beta 50-100 user 1 tuần trước go-live full marketing không?
