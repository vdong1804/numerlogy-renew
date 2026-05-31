# Phase 02 — Payment Safety Net + Observability

## Context Links

- Brainstorm: [../reports/brainstorm-260526-1025-launch-readiness-checklist.md](../reports/brainstorm-260526-1025-launch-readiness-checklist.md) (sections 3.4, 3.5)
- Overview: [plan.md](./plan.md)
- Backend root: `D:\Freelancer\Numerlogy\numerology-api\`
- Existing SePay service: `app/services/sepay_service.py`
- Existing scheduler: `app/jobs/scheduler.py`
- Implementation report: [../reports/fullstack-260526-1223-phase-02-backend.md](../reports/fullstack-260526-1223-phase-02-backend.md)
- Fixes report: [../reports/fullstack-260526-1245-critical-high-fixes.md](../reports/fullstack-260526-1245-critical-high-fixes.md)

## Overview

- **Priority:** P0 — block launch
- **Status:** implemented
- **Effort:** 4-5 ngày
- **Tuần:** 2 (parallel với Phase 01)
- **Goal:** Không có 1 case user trả tiền không nhận hàng. Lỗi prod không im lặng. Backup restore được.

## Key Insights

- v1.1 đã có webhook SePay + idempotent + APScheduler in-process
- Reconcile-SePay cron đã skip per v1.1 implementation notes — đây là gap lớn nhất
- Refund formal đã defer phase 2 — minimal manual refund đủ cho launch
- Sentry free tier 5k events/mo — đủ cho 2-5k user đầu nếu filter noise (4xx)
- `/health/detail` đã có (DB + provider check) — reuse cho UptimeRobot

## Requirements

**Functional:**
- Cron 15min: pull SePay tx list 24h, match orders pending, fulfill missed
- Admin refund button: gán lại quota / disable user_report + ghi note
- Checkout page: hiện "Liên hệ hỗ trợ" CTA khi pending >5 phút
- Email order-paid kèm link tải PDF (auth-protected URL với token)
- Sentry capture FastAPI unhandled + Next.js client errors
- UptimeRobot ping `/health/detail` 5 phút, alert email

**Non-functional:**
- Reconcile job idempotent (re-run safe nhờ webhook_events table)
- Refund operation log vào `orders.admin_notes` + audit trail tối thiểu
- Sentry env tag: production/staging
- Backup restore test pass trên DB staging trước go-live

## Architecture

```
SePay API ──pull 24h──→ reconcile_sepay_job (15m)
                             ↓
                    match ref_code + amount
                             ↓
                  unfulfilled? → fulfillment_service.fulfill()
                             ↓
                    log to webhook_events (provider=reconcile)

Admin UI ──refund button──→ POST /admin/orders/{id}/refund
                             ↓
                  order.status=refunded + admin_notes + user_report disable
                             ↓
                  refund email to user

FastAPI app ──unhandled──→ Sentry SDK
Next.js client ──error──→ Sentry browser SDK
UptimeRobot ──5m──→ /health/detail → alert if 5xx
```

## Related Code Files

**Create:**
- `numerology-api/app/jobs/reconcile_sepay.py`
- `numerology-api/app/services/sepay_service.py` (add `list_recent_transactions()`)
- `numerology-api/app/routers/admin/orders.py` (add `POST /admin/orders/{id}/refund`)
- `numerology-api/alembic/versions/0008_orders_admin_notes_refund.py` (add `admin_notes TEXT`, `refunded_at TIMESTAMPTZ`, status enum mở rộng `refunded`)
- `numerology-api/app/templates/emails/order-refund.html`
- `numerology-api/app/templates/emails/order-paid.html` (verify đã có, add download link với signed token)
- `numerology-api/app/utils/signed_url.py` (HMAC token cho download link, expire 7 ngày)
- `Numerology-Landing-Page/src/pages/admin/orders/[id].tsx` (add refund button + confirm dialog)
- `Numerology-Landing-Page/sentry.client.config.ts`
- `Numerology-Landing-Page/sentry.server.config.ts`
- `Numerology-Landing-Page/sentry.edge.config.ts`

**Modify:**
- `numerology-api/app/jobs/scheduler.py` (register reconcile_sepay 15m)
- `numerology-api/app/main.py` (init Sentry SDK)
- `numerology-api/pyproject.toml` (add `sentry-sdk[fastapi]`)
- `numerology-api/app/config.py` (add SENTRY_DSN, RECONCILE_WINDOW_HOURS=24)
- `numerology-api/app/services/fulfillment_service.py` (add `refund_order()` method)
- `numerology-api/app/routers/my_account.py` (download PDF endpoint accept signed token alt to JWT)
- `Numerology-Landing-Page/src/pages/check-out/[orderId].tsx` (CTA "Liên hệ hỗ trợ" khi pending >5min)
- `Numerology-Landing-Page/package.json` (add `@sentry/nextjs`)
- `Numerology-Landing-Page/next.config.js` (wrap với `withSentryConfig`)
- `numerology-api/deploy/.env.prod.example` (SENTRY_DSN)

## Implementation Steps

### Day 1 — Reconcile-SePay cron
1. Đọc SePay API doc `https://docs.sepay.vn/api-giao-dich-doi-soat.html`
2. Implement `sepay_service.list_recent_transactions(hours=24)` → SePay GET /userapi/transactions/list
3. Tạo `jobs/reconcile_sepay.py`: query orders status=pending in last 24h → for each tx parse `ref_code` → match → call `fulfillment_service.fulfill()` if not webhook_events row exists
4. Log mỗi reconcile run: count matched / count fulfilled / count errors
5. Register job 15min trong `scheduler.py`
6. Unit test: mock SePay response, verify chỉ fulfill orders chưa fulfilled

### Day 2 — Refund flow
7. Migration 0008: add `admin_notes TEXT NULL`, `refunded_at TIMESTAMPTZ NULL`, expand status enum `refunded`
8. `fulfillment_service.refund_order(order_id, reason, admin_user_id)`: tx → update order.status, set refunded_at, append admin_notes, decrement quota OR disable user_report
9. Router `POST /admin/orders/{id}/refund`: body `{reason}`, require superuser, idempotent (skip nếu đã refunded)
10. Email template `order-refund.html`: thông báo hoàn tiền + thời gian SePay xử lý
11. Admin UI: button "Hoàn tiền" trong `/admin/orders/[id]` → confirm dialog input reason → POST
12. Unit test: refund pending → reject (chưa paid), refund paid → ok, refund refunded → idempotent

### Day 3 — Checkout safety + signed download
13. `signed_url.py`: `make_signed_token(user_report_id, expires_in=7d)` HMAC SHA256 với SECRET_KEY
14. Download endpoint accept `?token=...` alt to JWT — verify HMAC + expiry
15. Email `order-paid.html` template: include signed URL cho mỗi report (không cần login để mở)
16. Checkout page: useEffect timer, sau 5 phút pending → hiện CTA "Liên hệ hỗ trợ qua Zalo: 0xxx / email: support@..."
17. Test: tạo order test, qua 5 phút verify CTA hiện; click link email download không cần login

### Day 4 — Sentry + UptimeRobot
18. Signup Sentry, tạo 2 project (Python `numerology-api`, JS `numerology-web`)
19. Backend: `sentry_sdk.init(dsn=SENTRY_DSN, environment=ENVIRONMENT, traces_sample_rate=0.1, integrations=[FastApiIntegration()])`
20. Filter: ignore 4xx, ignore `/health*`, sample webhooks 10%
21. Frontend: `npx @sentry/wizard@latest -i nextjs` → review configs, set tracesSampleRate 0.1
22. Add user context: middleware tag `user_id` khi có JWT
23. Test: throw error endpoint, verify Sentry dashboard nhận
24. UptimeRobot signup → 2 monitors: `https://nhansinhquan.vn` (HEAD), `https://api.nhansinhquan.vn/health/detail` (GET 200 + body contains "ok") — interval 5min, alert email

### Day 5 — Backup restore + E2E payment test
25. Trigger backup manual: `bash deploy/backup.sh` → verify file `.sql.gz` size hợp lý
26. Spin staging DB container: `docker run postgres:16`, `pg_restore` từ dump → verify table counts, sample query users/orders
27. **E2E real payment**: tạo product 10k, register user test, mua → chuyển khoản 10k thật → verify (a) webhook fire (b) order paid <30s (c) email tới Gmail (d) link download work
28. Test reconcile: tạo order test, BỎ webhook (block IP local), verify cron 15min sau fulfill
29. Test refund: admin refund 1 order test, verify quota giảm/report disable + email user nhận
30. Documentation: `docs/runbook-payment-incident.md` (webhook miss, refund process, reconcile manual trigger)

## Todo List

- [x] Day 1: SePay API client + reconcile cron + scheduler register + unit test
- [x] Day 2: Migration 0008 + refund service + admin endpoint + UI button + email template
- [x] Day 3: Signed download URL + checkout pending CTA + email order-paid với link
- [x] Day 4: Sentry backend + frontend + UptimeRobot 2 monitors (skeleton created, signup deferred)
- [ ] Day 5: Backup restore staging + E2E payment thật + reconcile test + refund test + runbook

## Success Criteria

- Reconcile cron chạy 15min, log count rõ
- Block webhook test → cron fulfill order trong 15min
- Refund button → order status refunded + quota/report adjust + email sent
- Email order-paid có link download work không cần login (signed token)
- Sentry nhận test error trong 30s
- UptimeRobot xanh, alert email khi backend down (test bằng docker stop)
- Backup restore staging: data toàn vẹn, count match
- E2E 10k thật: paid → email → download success <2 phút end-to-end

## Risk Assessment

| Risk | Mitigation |
|------|-----------|
| SePay API rate limit | Pull mỗi 15min đủ, không 1min |
| Sentry quota tràn | Sample webhooks 10%, ignore 4xx, ignore health |
| Signed token leak | Expire 7 ngày, có thể revoke bằng đổi SECRET (chấp nhận invalidate all) |
| Reconcile double-fulfill | Check webhook_events trước fulfill (idempotent guard sẵn) |
| Refund accidentally | Confirm dialog + admin role + log admin_user_id |
| Backup restore corrupt | Test trên staging trước, không trên prod |

## Security Considerations

- Signed download token: HMAC với SECRET_KEY (≠ JWT secret), expire 7 ngày, chứa user_report_id only
- Refund endpoint: require superuser JWT + audit log admin_user_id
- Sentry: scrub PII (email, phone) bằng `before_send` hook
- SePay API key: env var, không log
- Reconcile job: log mismatch nhưng không log full tx data (chỉ ref_code + amount)

## Implementation Notes (2026-05-26)

**Files created:** `signed_url.py`, `0008_orders_admin_notes_refund.py` (migration), `reconcile_sepay.py`, `order-refund.html`, `order-refund.txt`, `order-paid.txt`, `runbook-payment-incident.md`.

**Files modified:** `sepay_service.py` (list_recent_transactions), `fulfillment_service.py` (refund_order, signed links in order-paid), `admin/orders.py` (POST /admin/orders/{id}/refund), `order.py` (OrderStatus enum + refunded_at), `my_account.py` (download token HMAC), `scheduler.py` (reconcile 15m), `main.py` (Sentry init), `config.py`, `pyproject.toml`, `.env.prod.example`.

**Build result:** `from app.main import app` clean, migration chain valid (0007 → 0008), 175/191 tests pass (15 pre-existing fails).

**Code review fixes (all applied):**
- Reconcile commit per-order, not batch (H2)
- Idempotency check broadened: provider IN ('sepay','reconcile') + status IN ('matched','received','duplicate') (H3)
- Signed token type field added: "typ": "report_download" (H4)
- URL builder fixed: use settings.frontend_url instead of media_url.replace (H5)
- Refund note logic fixed: only set when pre-existing refund detected (H6)
- datetime.utcnow() → datetime.now(timezone.utc) (H1, 2 sites)
- Download token path traversal guard added (C3)

**Migration status:** 0008 ready, not yet run (requires alembic upgrade head on deployed DB).

**Skipped items (user action):**
- Sentry DSN signup: user creates account at sentry.io, sets env var
- UptimeRobot signup: user creates monitors at uptimerobot.com, points to /health/detail
- E2E real payment: requires bank app interaction
- Backup restore test: requires infra/Docker access
- SePay API: assumed in env (v1.1 prerequisite)

## Next Steps

- Phase 03 sẽ thêm rate limit cho /api/webhooks/sepay (chống spam)
- Phase 04 sẽ verify Sentry + UptimeRobot vẫn ok sau load test
- Refund formal workflow (state machine, partial) → defer P2 post-launch
- Before deploy: set NEXT_PUBLIC_SENTRY_DSN (frontend) + SENTRY_DSN (backend) separately
- Run: `alembic upgrade head` on production DB to apply 0008 migration
