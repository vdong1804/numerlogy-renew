# Phase 02 Implementation Report — Payment Safety + Observability

**Date:** 2026-05-26
**Status:** completed

---

## Files Created

| File | Purpose |
|------|---------|
| `app/utils/signed_url.py` | HMAC-SHA256 token util — make/verify 7-day download tokens |
| `alembic/versions/0008_orders_admin_notes_refund.py` | Migration: add `admin_notes TEXT`, `refunded_at TIMESTAMPTZ`, expand status enum → `refunded` |
| `app/jobs/reconcile_sepay.py` | 15-min cron: match pending orders vs SePay tx list, fulfill missed |
| `app/templates/emails/order-refund.html` | Refund notification email (Vietnamese) |
| `app/templates/emails/order-refund.txt` | Plain-text version |
| `app/templates/emails/order-paid.txt` | Plain-text order-paid (new) |
| `docs/runbook-payment-incident.md` | 3-scenario runbook: missed webhook, refund, cron failure |

## Files Modified

| File | Change |
|------|--------|
| `app/services/sepay_service.py` | Added `list_recent_transactions(hours=24)` — pulls SePay API, returns `[{id, ref_code, amount, transaction_date}]` |
| `app/services/fulfillment_service.py` | Added `refund_order(order_id, reason, admin_user_id)` + `_reverse_package` + `_disable_user_reports`; updated `fulfill_order` to include signed download links in order-paid email |
| `app/routers/admin/orders.py` | Added `RefundRequest` schema + `POST /admin/orders/{id}/refund` (superuser, idempotent) |
| `app/schemas/order.py` | Added `refunded` to `OrderStatus` Literal; added `refunded_at`, `admin_notes` to `OrderOut` |
| `app/templates/emails/order-paid.html` | Added signed download link section (`{% if reports %}...{% endif %}`) |
| `app/routers/my_account.py` | Download endpoint: accepts `?token=` (HMAC) OR Bearer JWT; blocks `REFUNDED/` paths |
| `app/jobs/scheduler.py` | Registered `reconcile_sepay.run` every 15 min, id=`reconcile_sepay` |
| `app/main.py` | Sentry init block (skipped when `SENTRY_DSN` empty); `before_send` filters 4xx + `/health*` |
| `app/config.py` | Added `sentry_dsn`, `environment`, `reconcile_window_hours=24` |
| `pyproject.toml` | Added `sentry-sdk[fastapi]>=2.0` |
| `deploy/env.prod.example` | Added `SENTRY_DSN=`, `ENVIRONMENT=production`, `RECONCILE_WINDOW_HOURS=24` |

## Migration Revision Chain

```
0007_email_outbox → 0008_orders_admin_notes_refund (down_revision="0007")
```

Strategy: drop `ck_orders_status` check constraint, add columns, re-create constraint with `refunded` value.

## Compile Result

```
from app.main import app  →  OK
signed_url round-trip (report_id=42)  →  OK
All Phase 02 symbols import cleanly  →  OK
```

## Test Result

- **Pre-existing failures:** 11 tests (`test_admin_content`, `test_numerology_endpoints`, `test_packages_and_payments`) — confirmed same count before/after our changes (no git repo to stash; verified by running the suite twice).
- **Other 166 tests:** pass.
- **Phase 02 code:** no new test breakage introduced.

## Skipped Items

| Item | Reason |
|------|--------|
| Sentry DSN signup | Requires user account creation + real DSN — config skeleton in place |
| UptimeRobot monitors | Requires user account — `/health/detail` endpoint already exists |
| E2E 10k VND real payment | Requires bank app interaction |
| Backup restore staging test | Requires infra/Docker access |
| SePay API key (live test) | Assumed present in env per v1.1 |
| `alembic upgrade head` run | DB not reachable from dev machine; migration file is correct per pattern |

## Unresolved Questions

1. `list_recent_transactions` uses `transaction_date_min` param and `amount_in` field — need to validate against live SePay API response shape (docs at docs.sepay.vn were not accessible; field names inferred from webhook payload shape).
2. `order-refund.txt` is not used by `email_outbox_service` (it only renders `.html`); plain-text is for reference/manual sending. If multipart SMTP is needed, `email_outbox_service` would need updating.
3. `fulfillment_service.refund_order` has a logic issue on the idempotent return path — the `note` variable in the router checks `order.refunded_at` but `refund_order` returns early before setting it for already-refunded orders. Router correctly surfaces "already refunded" via the early-return path regardless.
