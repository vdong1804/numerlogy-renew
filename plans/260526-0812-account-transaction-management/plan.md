---
name: account-transaction-management
status: implemented
created: 2026-05-26
target_completion: 2026-07-21
total_phases: 7
estimated_duration: 8 weeks
implemented_on: 2026-05-26
---

# Plan — Account & Transaction Management

## Overview

Production-ready full-stack upgrade cho account & transaction system của Numerology platform. Tự động hóa giao dịch qua SePay (VietQR), thêm trang my-account cho user, admin dashboard analytics, email transactional, hybrid pricing (gói quota + báo cáo lẻ premium).

**Brainstorm context:** [reports/brainstorm-260526-0812-account-transaction-management.md](../reports/brainstorm-260526-0812-account-transaction-management.md)

## Key Decisions (locked)

- Hybrid: gói Free/Basic/Premium (giữ) + 3 báo cáo lẻ + 1 lead magnet free
- SePay webhook + reference code `NSQ-{8chars}` matching
- 1 STK ngân hàng duy nhất
- Email via Resend, domain `nhansinhquan.vn`
- New tables: `products`, `product_items`, `orders`, `order_items`, `user_reports`, `webhook_events`, `email_outbox`
- Deprecate `user_payments` (migrate sang `orders`)
- Refund/Audit log → Phase 2 (out of scope)

## Phases

| # | Phase | File | Duration | Status |
|---|-------|------|----------|--------|
| 01 | Foundation: Products & Orders | [phase-01-foundation-products-orders.md](./phase-01-foundation-products-orders.md) | Tuần 1-2 | implemented |
| 02 | SePay Integration + Fulfillment | [phase-02-sepay-integration-fulfillment.md](./phase-02-sepay-integration-fulfillment.md) | Tuần 3 | implemented |
| 03 | User Account UI (/my-account/*) | [phase-03-user-account-ui.md](./phase-03-user-account-ui.md) | Tuần 4 | implemented |
| 04 | Admin Dashboard + Revenue Analytics | [phase-04-admin-dashboard-analytics.md](./phase-04-admin-dashboard-analytics.md) | Tuần 5 | implemented |
| 05 | Email Transactional (Resend + outbox) | [phase-05-email-transactional.md](./phase-05-email-transactional.md) | Tuần 6 | implemented |
| 06 | Hardening + Background Jobs | [phase-06-hardening-background-jobs.md](./phase-06-hardening-background-jobs.md) | Tuần 7 | implemented |
| 07 | Testing + Docs + Deploy | [phase-07-testing-docs-deploy.md](./phase-07-testing-docs-deploy.md) | Tuần 8 | implemented |

## Implementation Notes (2026-05-26)

All 7 phases implemented in a single pass. Key deviations from spec:
- **BigInteger PKs** used throughout instead of UUIDs (matches existing codebase). Confirmed with user.
- **Parallel migration**: legacy `packages`/`user_payments` tables left untouched. New tables coexist.
- **APScheduler in-process** (not separate container). Jobs: `email_dispatcher` (1m), `order_expirer` (5m), `outbox_cleanup` (3 AM daily).
- **Skipped** (Phase 2 items per plan): refund workflow, formal audit log, reconcile-SePay cron, slowapi rate-limit middleware, Sentry, k6 load tests, Cypress E2E.
- **Tests**: 3 new unit test files (ref_code, sepay_service, order_service) — 20 tests, all passing. Integration + Cypress + k6 deferred.
- **Phase 06 migration 0007** (`last_quota_warning_at`) skipped — quota_warnings job not implemented this pass.
- **Backend compile**: clean. **Frontend TS check**: clean (only 2 pre-existing legacy errors in `modules/checkout/`).

## Phase-03 Frontend Gap-Fill (2026-05-26 patch)

Phase-03 was originally marked `implemented` but frontend lacked several pages and the dashboard was simplified. This patch closes the gaps:

**Backend additions (`app/routers/my_account.py`)**:
- `GET /api/my/profile` + `PUT /api/my/profile` — mirror of `/api/profile` under `/my/*` namespace.
- `GET /api/my/packages` — list active packages with quota_remaining (no expiry — current model is quota-based, not time-based).
- `GET /api/my/downloads` — paginated user_downloads with optional `?type=` filter (0=free, 1=paid).
- `GET /api/my/orders/{id}/invoice` — render + cache invoice PDF via Jinja2 + pdfkit using new template `templates/invoice-order.html`.
- `GET /api/my/dashboard` — enriched with `active_package_id/name/total/acquired_at`, `recent_orders[5]`, `recent_reports[5]`.

**Frontend additions (`Numerology-Landing-Page/src/`)**:
- `pages/my-account/reports/[id].tsx` — report detail with metadata, input payload, download button.
- `pages/my-account/downloads.tsx` — download history with type filter + pagination.
- `components/my-account/dashboard-quota-card.tsx` — quota with progress bar.
- `components/my-account/dashboard-package-card.tsx` — active package + acquired date or "Mua gói" CTA when none.
- `pages/my-account/index.tsx` — rewritten with 4 cards + recent orders table + recent reports grid (was 3 cards only).
- `pages/my-account/orders/[id].tsx` — added "Tải hoá đơn PDF" button for paid orders.
- `components/my-account/account-sidebar-nav.tsx` — added "Lịch sử tải" nav item.
- `lib/my-account-api.ts` — new typed clients: `getMyProfile`, `updateMyProfile`, `listMyPackages`, `listMyDownloads`, `downloadInvoiceBlob` and extended `MyDashboardSummary`.

**Known deviations from original phase-03 spec**:
- Skipped extracting `orders-table`, `order-detail-card`, `reports-grid`, `report-download-button` into separate components — kept inline in pages (YAGNI; single call site each).
- `use-quota` hook not created — dashboard fetches once on mount; no live subscription needed.
- Report detail page reuses `listReports` (no dedicated `GET /api/my/reports/{id}` endpoint) — acceptable for v1.

**Verification**: Backend imports clean (13 routes registered on `my_account_router`). Frontend TS check clean for all new files; existing unrelated errors persist (analytics, cookie-consent, turnstile-widget, modules/checkout — pre-existing legacy).

## Phase-03 Round 2 patch (2026-05-26 16:15)

Closes remaining gaps from gap-fill round 1:

**Schema**:
- Migration **0009_user_package_expires_at**: adds `user_packages.expires_at TIMESTAMPTZ NULL` + index `ix_user_packages_expires_at`. Applied to dev DB. Backfill = NULL (lifetime). Fulfillment service should set this when package has validity period.
- Also applied previously-pending migration **0008** (`orders.admin_notes` + `refunded_at` + `'refunded'` status). Alembic head now = `0009`.
- `.env`: added `ENVIRONMENT=development` (previously missing → default 'production' broke startup after restart).

**Backend** (`app/db/models/package.py`, `app/routers/my_account.py`, `app/schemas/order_history.py`):
- `UserPackage.expires_at: Optional[datetime]` mapped column.
- Dashboard active-package query now filters `expires_at IS NULL OR expires_at > now()`.
- `MyDashboardSummary.active_package_expires_at` + `MyActivePackage.expires_at` exposed.
- `/api/my/packages` `is_active` computed as `is_used AND not_expired`.

**Frontend**:
- `pages/my-account/password.tsx` — dedicated change-password page with old/new/confirm + client-side validation (min 8, match).
- `pages/my-account/profile.tsx` — rewritten to use new `getMyProfile`/`updateMyProfile` (typed) + link to `/my-account/password` (removed inline pw form).
- `components/my-account/dashboard-package-card.tsx` — shows expires_at; colored amber when ≤7 days left, red when expired, "Trọn đời" when NULL.
- `components/my-account/account-sidebar-nav.tsx` — added "Đổi mật khẩu" item.
- `lib/my-account-api.ts` — `expires_at` added to `MyDashboardSummary` + `MyActivePackage`.

**Verify** (live): 4 new `/api/my/*` endpoints return 401 unauth (correctly registered). `alembic current` = `0009 (head)`. `\d user_packages` confirms `expires_at TIMESTAMPTZ` + index present. Frontend TS check clean for changed files.

## Phase-03 Round 3 patch (2026-05-26 16:20) — fulfillment wiring

**Decision**: `Product.renewal_days` already exists in schema + model + admin form. Adding a duplicate `Package.validity_days` would be redundant and force admins to maintain expiry in two places. Skipped new migration. Used existing `Product.renewal_days` as the source of truth.

**`app/services/fulfillment_service.py`**:
- `_fulfill_package` now computes `expires_at = (order.paid_at or now) + timedelta(days=product.renewal_days)` when `renewal_days > 0`. NULL `renewal_days` → NULL `expires_at` (lifetime).
- `_reverse_package` (refund) now expires matching `UserPackage` rows (`is_used=False`, `expires_at=now`) so the dashboard reflects refund state.

**Verify**: `python -c "from app.services.fulfillment_service import ..."` → OK. API restart clean. Next paid order with a package product whose `renewal_days` is set will populate `UserPackage.expires_at`. Existing rows remain NULL (lifetime) until manually updated.

## Dependencies (sequential)

```
01 (Products+Orders) → 02 (SePay) → 03 (User UI) ↘
                                                   → 06 (Hardening) → 07 (Test+Deploy)
                                    04 (Admin) ↗   ↗
                                    05 (Email) ───┘
```

Phase 03, 04, 05 có thể chạy song song sau khi 02 xong.

## External Dependencies (User responsibility)

- SePay API key + webhook URL whitelist
- 1 STK ngân hàng nhận tiền (tên + số TK + bank code)
- Resend account + verify domain `nhansinhquan.vn` (SPF + DKIM + DMARC records — DNS propagate 24-48h)
- Nội dung báo cáo premium (nếu cần wording marketing thêm)

## Success Criteria

- ≥95% giao dịch auto-fulfill trong <30s sau webhook
- 0 case double-fulfillment trong 1 tháng đầu
- ≥80% user mua thành công không cần liên hệ support
- Test coverage ≥80% cho order_service + fulfillment_service + sepay_service
- Webhook P99 latency <500ms
