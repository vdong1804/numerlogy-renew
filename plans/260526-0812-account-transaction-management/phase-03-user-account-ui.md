# Phase 03 — User Account UI (/my-account/*)

## Context Links
- [Plan overview](./plan.md)
- [Phase 01](./phase-01-foundation-products-orders.md), [Phase 02](./phase-02-sepay-integration-fulfillment.md)

## Overview
- **Priority:** P0 (user self-service, giảm support load)
- **Status:** pending
- **Duration:** Tuần 4 (5 ngày dev)
- **Description:** Tạo trang my-account cho user xem profile, lịch sử đơn, gói active, quota, thư viện báo cáo lẻ đã mua, lịch sử download. Backend read-only endpoints `/my/*`.

## Key Insights
- Hiện đã có `profile.py` router với `/profile/me` → mở rộng thành namespace `/my/*`
- Frontend đã có `_app.tsx`, auth state qua `lib/admin-auth.ts` (admin) → cần tạo `lib/user-auth.ts` cho client
- Reuse component pattern admin (table, pagination) cho lịch sử

## Requirements

### Functional
- `/my-account` dashboard: quota %, gói active + ngày hết hạn, link tới các tab
- `/my-account/profile`: edit name, birthday, gender, phone, address; đổi password
- `/my-account/orders`: list orders (filter status, paginate), click → detail
- `/my-account/orders/[id]`: chi tiết items, ref_code, paid_at, button download invoice PDF
- `/my-account/reports`: list user_reports, click → download PDF (vĩnh viễn)
- `/my-account/downloads`: history user_downloads (PDF từ quota gói)
- `/my-account/settings`: notification preferences toggle (chuẩn bị cho phase 5)

### Non-functional
- Auth guard: tất cả /my-account/* require JWT, redirect /login nếu thiếu
- Pagination: 20 items/page, server-side
- Mobile responsive (Tailwind)

## Architecture

### Backend `/my/*` namespace

```
GET /my/profile           → UserOut + ProfileOut
PUT /my/profile           → update name/birthday/gender/phone/address
POST /my/password         → change password (old + new)
GET /my/orders            → paginated list (filter: status, from_date, to_date)
GET /my/orders/{id}       → order detail with items
GET /my/orders/{id}/invoice → download invoice PDF (Jinja2 render on-demand)
GET /my/packages          → active packages with quota + expires_at
GET /my/reports           → list user_reports
GET /my/reports/{id}/download → stream PDF (verify ownership) + increment download_count
GET /my/downloads         → user_downloads history
GET /my/settings/notifications → notification prefs JSON
PUT /my/settings/notifications → update prefs
```

### Frontend structure

```
Numerology-Landing-Page/src/
├── pages/my-account/
│   ├── index.tsx           # dashboard
│   ├── profile.tsx         # profile edit
│   ├── password.tsx        # change password
│   ├── orders/
│   │   ├── index.tsx       # orders list
│   │   └── [id].tsx        # order detail
│   ├── reports/
│   │   ├── index.tsx       # reports library
│   │   └── [id].tsx        # report detail (preview + download)
│   ├── downloads.tsx       # downloads history
│   └── settings.tsx        # notification toggles
├── components/my-account/
│   ├── account-layout.tsx     # sidebar nav + topbar + auth guard
│   ├── account-sidebar-nav.tsx
│   ├── dashboard-quota-card.tsx
│   ├── dashboard-package-card.tsx
│   ├── orders-table.tsx       # reuse TanStack Table pattern
│   ├── order-detail-card.tsx
│   ├── reports-grid.tsx       # grid cards với cover image
│   └── report-download-button.tsx
├── lib/
│   ├── my-account-api.ts      # API client
│   └── user-auth.ts           # useUserAuth() hook (mirror admin-auth)
└── hooks/
    └── use-quota.ts           # subscribe quota changes
```

## Related Code Files

### Create
- `numerology-api/app/routers/my_account.py` — tất cả `/my/*` endpoints (rename profile.py internal?)
- `numerology-api/app/schemas/order_history.py`
- `numerology-api/app/schemas/notification_prefs.py`
- `numerology-api/app/services/invoice_service.py` — render invoice PDF from order
- `numerology-api/app/templates/invoice/order-invoice.html`
- `numerology-api/app/templates/invoice/base-invoice.html`
- `Numerology-Landing-Page/src/pages/my-account/index.tsx`
- `Numerology-Landing-Page/src/pages/my-account/profile.tsx`
- `Numerology-Landing-Page/src/pages/my-account/password.tsx`
- `Numerology-Landing-Page/src/pages/my-account/orders/index.tsx`
- `Numerology-Landing-Page/src/pages/my-account/orders/[id].tsx`
- `Numerology-Landing-Page/src/pages/my-account/reports/index.tsx`
- `Numerology-Landing-Page/src/pages/my-account/reports/[id].tsx`
- `Numerology-Landing-Page/src/pages/my-account/downloads.tsx`
- `Numerology-Landing-Page/src/pages/my-account/settings.tsx`
- `Numerology-Landing-Page/src/components/my-account/account-layout.tsx`
- `Numerology-Landing-Page/src/components/my-account/account-sidebar-nav.tsx`
- `Numerology-Landing-Page/src/components/my-account/dashboard-quota-card.tsx`
- `Numerology-Landing-Page/src/components/my-account/dashboard-package-card.tsx`
- `Numerology-Landing-Page/src/components/my-account/orders-table.tsx`
- `Numerology-Landing-Page/src/components/my-account/order-detail-card.tsx`
- `Numerology-Landing-Page/src/components/my-account/reports-grid.tsx`
- `Numerology-Landing-Page/src/components/my-account/report-download-button.tsx`
- `Numerology-Landing-Page/src/lib/my-account-api.ts`
- `Numerology-Landing-Page/src/lib/user-auth.ts`
- `Numerology-Landing-Page/src/hooks/use-quota.ts`

### Modify
- `numerology-api/app/routers/profile.py` — keep backward compat, alias to my_account
- `numerology-api/app/main.py` — register my_account router
- `numerology-api/app/db/models/user.py` — add `notification_prefs JSONB default={}` to user_profiles
- `numerology-api/alembic/versions/0006_add_notification_prefs.py` — NEW migration
- `Numerology-Landing-Page/src/components/admin/admin-topbar.tsx` — pattern reuse cho my-account topbar nếu phù hợp

## Implementation Steps

1. **Migration 0006** — add `user_profiles.notification_prefs JSONB DEFAULT '{}'::jsonb`
2. **Backend router `my_account.py`** — implement 11 endpoints (read-heavy, simple)
3. **`invoice_service.render_invoice(order_id) -> bytes`** — Jinja2 + wkhtmltopdf
4. **Templates** — base-invoice.html + order-invoice.html (logo, info công ty, items table, total)
5. **Pydantic schemas** — OrderHistoryOut, OrderDetailOut, NotificationPrefs, etc.
6. **Tests** — `test_my_account.py` cover ownership check (user A không xem được order user B)
7. **Frontend `user-auth.ts`** — useUserAuth() hook: fetch /auth/me, redirect /login nếu fail
8. **Frontend `my-account-api.ts`** — fetch wrapper với types
9. **Frontend `account-layout.tsx`** — sidebar nav + topbar + auth guard + children slot
10. **Dashboard page** — quota card (progress bar), active package card, recent orders 5, recent reports 5
11. **Profile + password pages** — react-hook-form + Zod validation
12. **Orders pages** — list table (filter status, search ref_code), detail page
13. **Reports pages** — grid card với cover image (placeholder hoặc generate thumbnail từ PDF page 1), download button
14. **Downloads page** — simple table
15. **Settings page** — toggles cho notification (lưu vào user_profiles.notification_prefs)
16. **Manual test** — flow đầy đủ user mua → vào my-account → xem đơn → tải lại PDF
17. **Mobile responsive check** — Tailwind responsive, test ở 375px width

## Todo List

- [ ] M1. Migration 0006 + run
- [ ] M2. Backend router my_account.py với 11 endpoints
- [ ] M3. invoice_service + templates invoice
- [ ] M4. Schemas order_history, notification_prefs
- [ ] M5. Tests test_my_account.py (ownership, pagination, filter)
- [ ] M6. Frontend lib/user-auth.ts + my-account-api.ts
- [ ] M7. Component account-layout + sidebar-nav
- [ ] M8. Dashboard page với 4 cards
- [ ] M9. Profile + password pages
- [ ] M10. Orders list + detail pages
- [ ] M11. Reports grid + detail pages
- [ ] M12. Downloads page
- [ ] M13. Settings notification toggles
- [ ] M14. Mobile responsive verify
- [ ] M15. E2E manual flow

## Success Criteria

- User login → vào /my-account thấy dashboard đầy đủ (quota, package, recent items)
- User chỉ xem được order/report của chính mình (test với 2 accounts)
- Pagination + filter hoạt động đúng (20 items/page)
- Download báo cáo lẻ tăng `download_count`
- Invoice PDF render đúng với info công ty + items + total
- Settings notification lưu được, đọc lại đúng
- Mobile 375px responsive OK (sidebar collapse thành drawer)

## Risk Assessment

| Risk | Mức | Mitigation |
|------|-----|-----------|
| Ownership check sai → user A xem được order user B | Cao | Test pattern: tất cả /my/* filter `user_id=current_user.id`; viết test 2-user explicit |
| /my-account namespace conflict với /profile cũ | Thấp | Giữ /profile cũ làm alias, deprecate sau 1 tháng |
| Performance: query orders + items + reports nặng | TB | Pagination 20 items; eager-load items với selectinload; index user_id |
| Invoice PDF render chậm (sync) làm timeout request | TB | Cache 1 lần render, lưu vào /media/invoices/{order_id}.pdf, lần sau serve static |
| Sidebar nav cho my-account khác admin → component duplication | Thấp | Tạo base `sidebar-nav-base.tsx` shared, two config sets |

## Security Considerations

- Tất cả `/my/*` require `get_current_user`
- Path traversal: `/my/reports/{id}/download` resolve path qua DB lookup, KHÔNG concat user input
- PDF download set `Content-Disposition: attachment; filename="..."`, MIME `application/pdf`
- Rate limit `/my/reports/{id}/download`: 10 req/phút/user (anti-abuse share link)
- Password change: verify old password trước, hash new với bcrypt, revoke all refresh tokens
- Notification prefs: validate JSON schema (chỉ allow known keys)

## Next Steps
- Có thể parallel với Phase 04, 05 sau Phase 02 xong
- Phase 06 sẽ thêm cron quota_low check (gửi notification dựa vào prefs trong settings)
