# Phase 04 Backend Implementation Report

## Files Created / Modified

| File | Action | LOC |
|------|--------|-----|
| `numerology-api/app/services/csv_export_service.py` | CREATE | 110 |
| `numerology-api/app/routers/admin/orders.py` | MODIFY | 194 |
| `docs/go-live-runbook.md` | CREATE | 144 |
| `docs/post-launch-monitoring.md` | CREATE | 130 |

## Query Params — GET /admin/orders

- `email` — partial match on User.email (ILIKE %value%)
- `ref_code` — partial match on Order.ref_code (ILIKE %value%)
- `status` — exact match, constrained to OrderStatus literal
- `date_from` — Order.created_at >= value (ISO 8601 datetime)
- `date_to` — Order.created_at <= value
- `page` — 1-based, default 1
- `page_size` — 1-100, default 20

GET /admin/orders/export.csv accepts same params minus pagination. Max 10 000 rows; returns 400 + message if exceeded.

## CSV Export Sample

```
order_id,ref_code,user_email,product_names,total_vnd,status,paid_at,refunded_at,created_at
1001,NSQ-AB123456,user@example.com,Bao cao than so hoc ca nhan,299000,paid,2026-05-25 09:14:33,,2026-05-25 09:10:01
```

UTF-8 BOM (`\xef\xbb\xbf`) prepended. Semicolons separate multiple products per order.

## Runbook Sections

**go-live-runbook.md** — 5 sections: Pre-flight Checklist (16 items), Deploy Steps (12 steps), Rollback Triggers, Rollback Procedure, Comms Plan  
**post-launch-monitoring.md** — 5 sections: Dashboard Links, Daily Checks, Weekly Checks, Alert Thresholds, Escalation Contacts + Incident Playbook References

## Compile / Test

- `python -c "from app.main import app"` — PASS
- AST syntax check orders.py + csv_export_service.py — PASS
- `pytest -k 'order or csv or export'` — 3 passed, 0 failed
- Full suite — 17 failed / 173 passed (matches Phase 03 baseline; 0 regressions introduced)

Bug fixed during implementation: `status` query param shadowed `fastapi.status` module in `export_orders`. Resolved by importing as `http_status` and replacing all usages.

## Skipped (User Actions)

- Blog 5-10 bài content — user soạn qua admin News CRUD
- Cloudflare DNS + proxy setup — user dashboard action
- Soft launch beta invite list — user
- Mobile QA real device — user
- Final E2E smoke + ads enable — user go-live day
- Admin lint cleanup sprint — defer post-launch
- `docs/beta-feedback-log.md` — not in file ownership scope

## Unresolved Questions

- `refunded_at` field: not present in `Order` model (`orders` table). `OrderOut` schema references it. `csv_export_service` uses `getattr(order, 'refunded_at', None)` as fallback — safe but will always be empty until migration adds the column. Confirm if Phase 01/02 migration added it, or schedule `ALTER TABLE orders ADD COLUMN refunded_at TIMESTAMPTZ`.
- Export route `/orders/export.csv` placed before `/orders/{order_id}` in router — FastAPI matches routes in declaration order so this is correct, but verify the admin router prefix does not conflict with a catch-all elsewhere.
