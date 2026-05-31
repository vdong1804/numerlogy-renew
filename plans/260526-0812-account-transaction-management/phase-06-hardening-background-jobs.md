# Phase 06 — Hardening + Background Jobs

## Context Links
- [Plan overview](./plan.md)
- [Phase 02](./phase-02-sepay-integration-fulfillment.md), [Phase 05](./phase-05-email-transactional.md)

## Overview
- **Priority:** P1 (production reliability)
- **Status:** pending
- **Duration:** Tuần 7 (5 ngày dev)
- **Description:** Cron jobs (expire orders, quota low, package expiring, reconcile SePay, cleanup outbox), rate limiting, Sentry monitoring, webhook IP whitelist, health checks chi tiết.

## Key Insights
- APScheduler in-process đơn giản nhất (no extra container), chạy trong FastAPI startup → tradeoff: nếu API restart job có thể skip 1 tick
- Alternative: standalone scheduler container chạy `cron` + python scripts → ổn định hơn
- Recommend: APScheduler cho jobs nhẹ (<1min interval), separate container cho jobs nặng (PDF batch, reconcile)
- slowapi rate limiting đã có pattern trong FastAPI community

## Requirements

### Functional
- **Cron jobs:**
  1. `expire_pending_orders` — mỗi 5 phút, status=expired cho orders pending quá expires_at; enqueue order_expired email
  2. `check_quota_warnings` — mỗi giờ, gửi quota_low email khi user remaining/total < 20% và chưa gửi trong 7 ngày
  3. `check_package_expiry` — mỗi ngày 7AM, gửi package_expiring email khi expires_at trong 3 ngày
  4. `reconcile_sepay` — mỗi 30 phút, gọi SePay API list-transactions 1h gần nhất, match với orders pending mà chưa có webhook
  5. `cleanup_outbox` — mỗi ngày 3AM, xóa email_outbox status=sent với sent_at < NOW-30d
  6. `cleanup_webhook_events` — mỗi tuần, xóa webhook_events status=duplicate/unmatched với processed_at < NOW-90d
- **Rate limiting:**
  - POST /orders: 10/phút/user
  - POST /webhooks/sepay: 100/phút/IP, bypass cho SEPAY_WEBHOOK_IP_WHITELIST
  - POST /auth/login: 5/phút/IP
  - GET /my/reports/{id}/download: 10/phút/user
- **Monitoring:**
  - Sentry SDK integrate, capture exceptions
  - /health endpoint detail: DB ping, Resend reachable, SePay API reachable (optional)
- **Webhook security:** IP whitelist enforcement nếu env set

### Non-functional
- Job runs không block API requests (separate event loop hoặc thread pool)
- Sentry không capture sensitive data (filter PII)
- Health check <100ms

## Architecture

### APScheduler in FastAPI

```python
# app/jobs/scheduler.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler(timezone='Asia/Bangkok')

def setup_jobs(scheduler):
    scheduler.add_job(expire_pending_orders, 'interval', minutes=5)
    scheduler.add_job(check_quota_warnings, 'interval', hours=1)
    scheduler.add_job(check_package_expiry, 'cron', hour=7, minute=0)
    scheduler.add_job(reconcile_sepay, 'interval', minutes=30)
    scheduler.add_job(cleanup_outbox, 'cron', hour=3, minute=0)
    scheduler.add_job(cleanup_webhook_events, 'cron', day_of_week='sun', hour=4)
    scheduler.add_job(email_dispatcher.run, 'interval', minutes=1)

# main.py lifespan
@asynccontextmanager
async def lifespan(app):
    setup_jobs(scheduler)
    scheduler.start()
    yield
    scheduler.shutdown()
```

### Backend structure

```
numerology-api/app/
├── jobs/
│   ├── scheduler.py                       # NEW: APScheduler setup
│   ├── expire_pending_orders_job.py       # NEW
│   ├── check_quota_warnings_job.py        # NEW
│   ├── check_package_expiry_job.py        # NEW
│   ├── reconcile_sepay_job.py             # NEW
│   ├── cleanup_outbox_job.py              # NEW
│   ├── cleanup_webhook_events_job.py      # NEW
│   └── email_dispatcher_job.py            # (Phase 5, register here too)
├── middleware/
│   ├── rate_limit.py                      # NEW: slowapi config
│   └── sentry.py                          # NEW: Sentry init
├── routers/
│   └── health.py                          # NEW (detail health check)
└── services/
    ├── sepay_client.py                    # NEW: SePay API client (for reconcile)
    └── quota_warning_service.py           # NEW: logic decide who to warn
```

## Related Code Files

### Create
- `numerology-api/app/jobs/scheduler.py`
- `numerology-api/app/jobs/expire_pending_orders_job.py`
- `numerology-api/app/jobs/check_quota_warnings_job.py`
- `numerology-api/app/jobs/check_package_expiry_job.py`
- `numerology-api/app/jobs/reconcile_sepay_job.py`
- `numerology-api/app/jobs/cleanup_outbox_job.py`
- `numerology-api/app/jobs/cleanup_webhook_events_job.py`
- `numerology-api/app/middleware/__init__.py`
- `numerology-api/app/middleware/rate_limit.py`
- `numerology-api/app/middleware/sentry.py`
- `numerology-api/app/routers/health.py`
- `numerology-api/app/services/sepay_client.py`
- `numerology-api/app/services/quota_warning_service.py`
- `numerology-api/tests/test_jobs/test_expire_pending_orders.py`
- `numerology-api/tests/test_jobs/test_check_quota_warnings.py`
- `numerology-api/tests/test_jobs/test_reconcile_sepay.py`
- `numerology-api/tests/test_jobs/test_cleanup_jobs.py`
- `numerology-api/tests/test_rate_limit.py`

### Modify
- `numerology-api/app/main.py` — lifespan với scheduler startup; integrate slowapi + Sentry middleware
- `numerology-api/app/config.py` — add SENTRY_DSN, RATE_LIMIT_ENABLED
- `numerology-api/app/routers/orders.py` — add `@limiter.limit("10/minute")` cho POST
- `numerology-api/app/routers/webhooks.py` — add IP whitelist check + rate limit
- `numerology-api/app/routers/auth.py` — add rate limit login
- `numerology-api/app/routers/my_account.py` — rate limit download endpoint
- `numerology-api/pyproject.toml` — add deps: `apscheduler`, `slowapi`, `sentry-sdk[fastapi]`, `httpx` (đã có)
- `numerology-api/.env.example` — add SENTRY_DSN, RATE_LIMIT_ENABLED, SEPAY_API_BASE
- `numerology-api/app/db/models/user.py` — add `last_quota_warning_at datetime NULL` to user_profiles (anti spam)
- `numerology-api/alembic/versions/0007_quota_warning_tracking.py` — NEW

## Implementation Steps

1. **Migration 0007** — add `user_profiles.last_quota_warning_at`
2. **Dependencies** — add apscheduler, slowapi, sentry-sdk vào pyproject
3. **`scheduler.py`** — AsyncIOScheduler config + setup_jobs function
4. **Job `expire_pending_orders`**:
   - Query: `UPDATE orders SET status='expired' WHERE status='pending' AND expires_at < NOW() RETURNING id, user_id`
   - For each → enqueue email order_expired
5. **Job `check_quota_warnings`**:
   - Query users với quota remaining < 20% AND (last_warning_at IS NULL OR < NOW-7d)
   - For each → check notification_prefs.quota_warnings != false → enqueue email + update last_warning_at
6. **Job `check_package_expiry`**:
   - Query user_packages WHERE expires_at BETWEEN NOW AND NOW+3d
   - For each → enqueue email package_expiring
7. **`sepay_client.py`** — async GET `https://my.sepay.vn/userapi/transactions/list` với date range, Bearer token
8. **Job `reconcile_sepay`**:
   - Get last 1h transactions from SePay API
   - For each: try parse ref_code → match order pending → if found, process như webhook (idempotent via sepay_tx_id)
   - Useful khi webhook miss
9. **Job `cleanup_outbox`** — `DELETE FROM email_outbox WHERE status='sent' AND sent_at < NOW - INTERVAL '30 days'`
10. **Job `cleanup_webhook_events`** — `DELETE FROM webhook_events WHERE status IN ('duplicate','unmatched') AND processed_at < NOW - INTERVAL '90 days'`
11. **Lifespan integrate** — main.py startup scheduler, shutdown cleanly
12. **Rate limit middleware** — slowapi setup, decorator endpoints critical
13. **IP whitelist webhook** — middleware check `request.client.host` against `SEPAY_WEBHOOK_IP_WHITELIST` (comma-separated CIDRs)
14. **Sentry init** — `sentry_sdk.init(dsn=..., integrations=[FastApiIntegration, SqlalchemyIntegration], traces_sample_rate=0.1)`; filter `before_send` để strip password/JWT
15. **Health endpoint** — `/health`: liveness; `/health/detail`: DB ping + Resend reach + (optional) SePay reach
16. **Tests** — mock time với freezegun, verify jobs trigger đúng condition
17. **Test rate limit** — 11 requests/phút trả 429
18. **Test IP whitelist** — request từ IP không trong whitelist trả 403
19. **Manual ops test** — restart container, verify jobs reschedule; check Sentry catch 1 error test
20. **Doc** — viết runbook `docs/operations-runbook.md` (cron schedule, rate limit, troubleshoot)

## Todo List

- [ ] M1. Migration 0007 last_quota_warning_at
- [ ] M2. Add deps: apscheduler, slowapi, sentry-sdk
- [ ] M3. scheduler.py + setup_jobs
- [ ] M4. Job expire_pending_orders
- [ ] M5. Job check_quota_warnings + quota_warning_service
- [ ] M6. Job check_package_expiry
- [ ] M7. sepay_client + Job reconcile_sepay
- [ ] M8. Job cleanup_outbox + cleanup_webhook_events
- [ ] M9. main.py lifespan integrate scheduler
- [ ] M10. Rate limit middleware + decorator endpoints
- [ ] M11. IP whitelist webhook middleware
- [ ] M12. Sentry init + before_send filter PII
- [ ] M13. Health endpoint /health + /health/detail
- [ ] M14. Tests jobs (5 files)
- [ ] M15. Test rate_limit + IP whitelist
- [ ] M16. Operations runbook docs

## Success Criteria

- Scheduler start với app, 7 jobs registered và chạy đúng interval
- Expire orders job: tạo order pending → fake expires_at past → run job → order status=expired + email enqueued
- Quota warning: setup user quota 15% → run job → email enqueued + last_warning_at updated
- Reconcile SePay: mock SePay API response → 1 transaction match → order paid + fulfilled
- Cleanup: tạo 100 rows old → run job → còn 0 rows old
- Rate limit: 11 POST /orders/phút từ 1 user → request thứ 11 trả 429
- IP whitelist webhook: request từ IP ngoài whitelist → 403
- Sentry: throw test exception → thấy trong Sentry dashboard, no PII leak
- /health/detail 200 với JSON `{db: ok, resend: ok, sepay: ok}`

## Risk Assessment

| Risk | Mức | Mitigation |
|------|-----|-----------|
| APScheduler in-process miss tick khi restart | TB | Jobs đều idempotent (check condition trước action); accept miss 1 tick OK |
| Reconcile SePay double-process khi webhook đến cùng lúc | TB | Idempotency qua `webhook_events.sepay_tx_id` UNIQUE đã handle |
| Rate limit false positive cho user thật (vd dùng VPN share IP) | TB | Rate limit by user_id cho authenticated endpoints, by IP cho public; có button "Liên hệ support" |
| Sentry quota miễn phí 5k events/tháng vượt | TB | Filter spam events, traces_sample_rate=0.1; upgrade paid nếu cần |
| Scheduler block event loop với job nặng | Cao | Jobs dùng async DB session, không CPU-bound; offload PDF render qua BackgroundTasks |
| Cleanup job xóa nhầm data còn cần | Cao | DRY RUN trước (LOG count), schedule outside peak hours; backup DB daily đã có |
| SePay API token rotate → reconcile fail | TB | Alert nếu 3 lần liên tiếp fail; doc rõ thay token |

## Security Considerations

- Sentry `before_send` filter: strip `Authorization` header, password fields, JWT tokens trong stack trace
- IP whitelist parse cẩn thận (CIDR notation), default empty = no restriction (dev OK, prod required)
- Rate limit store: Redis nếu multi-instance, in-memory cho single VPS
- /health/detail: KHÔNG leak version số, internal hostname; chỉ {ok/fail}
- Cron jobs run với DB user same as API (no superuser) → least privilege
- Backup script lưu file backup encrypted (gpg) nếu compliance yêu cầu

## Next Steps
- Phase 07: testing toàn diện + deploy
- Future Phase 2: thêm Redis cho rate limit + cache, Prometheus metrics, audit log table
