# Phase 04 — Content/SEO + Admin Ops + Buffer + Go-Live

## Context Links

- Brainstorm: [../reports/brainstorm-260526-1025-launch-readiness-checklist.md](../reports/brainstorm-260526-1025-launch-readiness-checklist.md) (sections 4.3, 4.4 + section 6 lịch)
- Overview: [plan.md](./plan.md)
- Implementation reports: fullstack-260526-1350-phase-04-{backend,frontend}.md; fullstack-260526-1420-phase-04-fixes.md; code-reviewer-260526-1410-phase-04-review.md; tester-260526-1410-phase-04-validation.md

## Overview

- **Priority:** P1 + go-live
- **Status:** implemented
- **Effort:** 5-7 ngày
- **Tuần:** 4
- **Goal:** Admin ops + image SEO infra complete. Content/Cloudflare/soft-launch = user actions. Backend/frontend code-able portion shipped.

## Key Insights

- Phase 01-03 đã ship đủ infra; tuần này = content + polish + go-live procedure
- Soft launch trước 1 tuần beta giảm 80% risk vs big-bang
- Cloudflare proxy + DDoS + CDN free → no-brainer, chỉ cần đổi nameserver
- Blog content vừa cho SEO long-tail vừa cho ads landing
- Admin export CSV bắt buộc khi báo cáo VAT/thuế cuối tháng

## Requirements

**Content & SEO:**
- 5-10 bài blog seed cho long-tail keyword
- Internal linking blog → shop CTA
- Image alt text mọi `<img>`
- `next/image` cho ảnh ≥100KB
- Cloudflare CDN + DNS proxy

**Admin ops:**
- Export orders CSV (filter date range)
- Search/filter orders nâng cao (email, ref_code, status, date)
- Daily revenue summary verify trong dashboard
- Mark-as-paid bulk (optional)

**Go-live:**
- Soft launch 50-100 beta user, thu feedback 5-7 ngày
- Production deploy cutover
- Monitor 24h sau public launch
- Rollback procedure verify

## Architecture

```
Blog content (admin News CRUD) → /post/[id]
        ↓ JSON-LD Article + internal links → /shop
        
Cloudflare DNS proxy ──→ origin nginx
   ├── CDN cache static
   ├── DDoS L3/L4 protect
   └── Turnstile (đã setup Phase 03)

Admin /admin/orders → search params + CSV export endpoint

Soft launch (beta list) ──5-7d feedback──→ fix critical
       ↓
Public launch (ads on) ──24h monitor──→ Sentry + UptimeRobot dashboard
```

## Related Code Files

**Create:**
- `numerology-api/app/routers/admin/orders.py` (add `GET /admin/orders/export.csv` + search params)
- `numerology-api/app/services/csv_export_service.py`
- `Numerology-Landing-Page/src/pages/admin/orders/index.tsx` (search/filter form + export button)
- 5-10 file blog content (qua admin News CRUD, không code)
- `docs/go-live-runbook.md`
- `docs/post-launch-monitoring.md`
- `docs/beta-feedback-log.md`

**Modify:**
- `numerology-api/app/routers/admin/orders.py` (extend search: email, ref_code, status, date_from, date_to)
- `Numerology-Landing-Page/src/lib/admin-dashboard-api.ts` (CSV endpoint, search params)
- Existing pages: replace `<img>` → `<Image>` cho hero/blog/shop images ≥100KB
- All `<img>` add `alt=` attr (a11y + SEO)
- DNS panel: switch nameserver → Cloudflare
- Cloudflare dashboard: enable proxy `nhansinhquan.vn` + `api.nhansinhquan.vn`, set SSL Full (strict), enable caching tĩnh

## Implementation Steps

### Day 1 — Admin ops
1. Extend `/admin/orders` query params: `?email=&ref_code=&status=&date_from=&date_to=&page=`
2. `csv_export_service.export_orders(filters)` → CSV bytes với header: order_id, ref_code, user_email, product_names, total_vnd, status, paid_at, created_at
3. Endpoint `GET /admin/orders/export.csv` → StreamingResponse, require superuser
4. Admin UI: search form (email input, ref_code input, status dropdown, date range picker) + "Xuất CSV" button → `<a download>` link
5. Verify dashboard `/admin/dashboard` có revenue summary today/yesterday/this-week/this-month (đã có v1.1 — chỉ verify)
6. Test export 100 orders → CSV mở Excel UTF-8 BOM đúng tiếng Việt

### Day 2 — SEO content & image
7. Image alt text audit: grep `<img` mọi `.tsx` → fill `alt=` (mô tả nội dung, không "image")
8. Replace `<img>` → `next/image` cho ảnh ≥100KB (hero banner, shop covers, blog thumbnails)
9. Lighthouse re-audit mobile target ≥85 (đã làm Phase 03 day 5, verify post image fix)
10. Sitemap re-gen sau build, verify count match pages

### Day 3 — Blog content (5-10 bài)
11. Brief: long-tail keywords list (qua Google Suggest, AnswerThePublic)
   - "số chủ đạo là gì", "ý nghĩa số 8 trong thần số học", "cách tính số đường đời", "số sứ mệnh và ý nghĩa", "thần số học tình yêu", "số thái độ trong thần số học", "ý nghĩa số 11 master number", "thần số học sự nghiệp", "biểu đồ ngày sinh thần số học", "số trưởng thành ý nghĩa"
12. Soạn 5-10 bài ≥800 chữ, có outline H2/H3, internal link tới `/shop/[slug]` báo cáo tương ứng
13. Upload qua admin /news/new — featured image, slug SEO-friendly
14. Verify mỗi bài có JSON-LD Article (Phase 01 đã add)
15. Add CTA cuối mỗi bài → "Xem báo cáo chi tiết tại Shop"

### Day 4 — Cloudflare CDN setup
16. Cloudflare signup, add `nhansinhquan.vn` site
17. Update nameserver tại registrar → Cloudflare NS (propagate 1-24h)
18. Enable proxy orange cloud cho `@`, `www`, `api`
19. SSL/TLS mode: Full (strict) — yêu cầu origin cert valid (Let's Encrypt đã có)
20. Page Rules: cache static `/static/*`, `/_next/static/*` edge cache 1 năm
21. Caching rules: bypass `/api/*`, `/admin/*`, `/my-account/*`
22. Verify rate limit vẫn work: backend đọc `CF-Connecting-IP` thay vì `X-Forwarded-For` (cập nhật `slowapi` key_func nếu cần)
23. Test: speedtest before/after Cloudflare → expect cải thiện TTFB
24. Verify Sentry/UptimeRobot vẫn xanh sau Cloudflare on

### Day 5 — Go-live runbook + soft launch
25. Soạn `docs/go-live-runbook.md`:
   - Pre-flight checklist (10 mục: backup mới, restore test pass, Sentry quiet, UptimeRobot xanh, SSL Labs A, DNS resolve, etc.)
   - Deploy steps (pull → migrate → restart → smoke test)
   - Rollback trigger conditions + procedure
   - Comms plan (announcement to beta users)
26. Tạo beta user list (50-100): mời qua email + Zalo group
27. Soft launch: deploy prod stable, gửi invite, monitor 24h Sentry + UptimeRobot
28. `docs/beta-feedback-log.md` tracking: bug found, severity, fix status
29. Fix critical bugs trong 3-5 ngày beta

### Day 6 — Post-beta fixes + public launch prep
30. Triage beta feedback: fix P0/P1, defer P2
31. Final smoke test: register → mua → checkout → email → download → admin refund (mỗi flow lần cuối)
32. Pre-launch checklist run-through:
   - [ ] Sentry quiet (no errors 24h)
   - [ ] UptimeRobot 100% 24h
   - [ ] Backup mới nhất <24h
   - [ ] SSL Labs A
   - [ ] securityheaders A
   - [ ] Lighthouse mobile ≥85
   - [ ] DNS Cloudflare proxy xanh
   - [ ] Sitemap submitted GSC
   - [ ] GA4 + Pixel test events fire
   - [ ] Legal pages tất cả accessible
   - [ ] Email mail-tester ≥9
   - [ ] Reconcile cron chạy ok 15min
   - [ ] Refund flow tested
   - [ ] Rate limit verified
   - [ ] Turnstile work
33. `docs/post-launch-monitoring.md`: dashboard links + alert thresholds + escalation contact

### Day 7 — Public launch + monitor
34. Bật ads (FB/Google) với budget nhỏ ngày đầu (warm-up traffic)
35. Monitor real-time 24h: Sentry error rate, UptimeRobot uptime, GA4 conversion, SePay tx success rate
36. Hotfix nếu critical (rollback procedure ready)
37. Daily standup mỗi sáng tuần đầu launch để review metrics

## Todo List

- [x] Day 1: Admin orders search/filter + CSV export + dashboard verify (IMPLEMENTED 2026-05-26)
- [x] Day 2: Image alt text + next/image + Lighthouse re-check + sitemap re-gen (IMPLEMENTED 2026-05-26)
- [ ] Day 3: 5-10 blog bài seed + internal linking + CTA shop (USER ACTION: via admin News CRUD)
- [ ] Day 4: Cloudflare DNS + proxy + SSL Full + Page Rules + IP fix slowapi (USER ACTION: registrar + Cloudflare dashboard)
- [x] Day 5: Go-live runbook + post-launch-monitoring doc (IMPLEMENTED 2026-05-26; soft-launch/monitor = USER ACTION)
- [ ] Day 6: Beta fixes + final smoke test + pre-launch checklist (USER ACTION: after soft launch)
- [ ] Day 7: Public launch + ads on + 24h monitor (USER ACTION: go-live execution)

## Success Criteria

- CSV export 1000 orders <5s, mở Excel tiếng Việt đúng
- Lighthouse mobile ≥85 sau image fix
- 5+ blog bài live, có JSON-LD Article, internal link
- Cloudflare proxy xanh, TTFB cải thiện ≥30%
- SSL Labs vẫn A sau Cloudflare
- Soft launch 50 user, ≥80% complete flow, ≤5 bug critical
- Pre-launch checklist 100% tick
- Public launch 24h: 0 sự cố critical, Sentry error rate <0.5%, uptime ≥99.5%

## Risk Assessment

| Risk | Mitigation |
|------|-----------|
| Cloudflare proxy break rate limit (wrong IP) | Update slowapi đọc `CF-Connecting-IP`, test 429 |
| Cloudflare cache leak private route | Page Rules bypass `/api/*`, `/admin/*`, `/my-account/*` explicit |
| Blog content thin (Google ignore) | Tối thiểu 800 chữ, original, có hình + structure tốt |
| Beta user phát hiện bug critical | 5 ngày fix + buffer 1 ngày + rollback procedure ready |
| Ads spike traffic vượt server | Cloudflare cache đỡ + rate limit + scale up nếu cần |
| DNS nameserver swap downtime | Propagate vài giờ, tăng TTL trước, swap off-hour |

## Security Considerations

- Cloudflare SSL Full (strict) — không Flexible (man-in-middle risk)
- Origin server vẫn block port 80/443 từ non-Cloudflare IP (firewall rule, optional)
- CSV export endpoint require superuser, log admin_user_id
- Blog content admin-only edit (existing News CRUD permission)
- Soft launch: invite-only, không public URL share

## Implementation Notes (2026-05-26)

**Code-able subset implemented (concurrent Day 1-2 activities).**

Backend (csv_export_service.py, orders.py extended):
- `/admin/orders` params: email (ILIKE escape), ref_code, status, date_from/date_to (Bangkok TZ contract), page/page_size
- `/admin/orders/export.csv` StreamingResponse, UTF-8 BOM, max 10k rows, formula-injection safeguard
- go-live-runbook.md: 5 sections (pre-flight 16 items, deploy 12 steps, rollback triggers, comms), 144 LOC
- post-launch-monitoring.md: daily/weekly checks, alert thresholds, escalation contacts, 130 LOC

Frontend (admin-dashboard-api.ts, orders/index.tsx, order-search-form.tsx):
- searchOrders + exportOrdersCsv typed API wrappers
- admin/orders/index.tsx rewritten 175 LOC: 5-field search form + CSV export + empty state + pagination
- order-search-form.tsx extracted 110 LOC: Email/ref_code/status/date range inputs
- image-audit.md: 10 img tags, fixed alt on zodiac/satellite/adalash_banner, migrated bg-teacher (627KB) + adalash_banner (317KB) to next/image

Code Review (7.5/10 → fixed):
- C1: http_http_status typo line 145 (NameError → 500) → fixed
- H1: ILIKE wildcard escape + max_length 200 (perf DoS prevention) → escape_like helper added
- H2: CSV formula injection (`=+-@\t\r` prefix) → _safe_csv_cell applied
- H3: DatePicker Bangkok UTC (date_from/date_to TZ contract) → toIsoWithBangkokTz helper
- H4: CSV 10k bounded comment added
- H5: exportOrdersCsv error UX (JSON detail extraction) → fixed

Test: 173/190 pass (17 pre-existing, 0 regressions)

**User Actions Required (blocking go-live):**
- Blog 5-10 bài seed content via admin News CRUD (SEO long-tail, 800+ words, JSON-LD, internal links)
- Cloudflare signup → add site → change registrar nameservers (24-48h propagate) → enable proxy + SSL Full
- Soft launch: invite 50-100 beta users, monitor 5-7d, fix P0/P1
- Mobile QA real device iOS/Android
- Final E2E smoke test (register/pay/download/refund flow)
- Enable ads (FB/Google) + 24h launch monitor
- Admin lint cleanup sprint deferred to post-launch backlog

**Related Implementation Reports:**
- fullstack-260526-1350-phase-04-backend.md (csv_export_service, orders.py, runbooks)
- fullstack-260526-1350-phase-04-frontend.md (admin-dashboard-api, orders UI, image audit)
- code-reviewer-260526-1410-phase-04-review.md (7.5/10, critical + high findings)
- tester-260526-1410-phase-04-validation.md (173/190 pass, validation results)
- fullstack-260526-1420-phase-04-fixes.md (applied all critical + high fixes)

## Next Steps (Post-Launch)

- Tuần 5+: monitor metrics daily, tune rate limits, fix beta feedback P2
- Tháng 2: CI/CD GitHub Actions, audit log, refund formal workflow
- Tháng 3+: Redis cache, k6 load test, mobile app planning
- Quý sau: 2FA admin, Prometheus + Grafana, audit dashboard

## Out of Scope

- Mobile app
- Multi-tenancy
- Real-time WebSocket
- Audit log formal (P2)
- Refund state machine (P2)
- i18n (đã setup chưa dùng)
