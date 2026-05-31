# Phase 04 — Admin Dashboard + Revenue Analytics

## Context Links
- [Plan overview](./plan.md)
- [Phase 01](./phase-01-foundation-products-orders.md), [Phase 02](./phase-02-sepay-integration-fulfillment.md)

## Overview
- **Priority:** P1 (admin productivity, business insights)
- **Status:** pending
- **Duration:** Tuần 5 (5 ngày dev)
- **Description:** Mở rộng admin với dashboard KPI doanh thu real-time, biểu đồ revenue 30 ngày, top products, filter giao dịch nâng cao, export CSV, button manual mark-paid.

## Key Insights
- Hiện đã có `dashboard-charts.tsx`, `dashboard-recent-payments.tsx`, `dashboard-stat-card.tsx` → reuse/refactor
- Admin layout, sidebar, command palette đã hoàn chỉnh → chỉ thêm pages mới
- TanStack Table đã setup → dùng cho orders table với advanced filter

## Requirements

### Functional
- `/admin/dashboard` (cập nhật): cards (Doanh thu hôm nay/tuần/tháng, Đơn pending, Đơn paid, MRR ước tính, Báo cáo lẻ bán/tuần), biểu đồ revenue 30 ngày (line chart), top 5 products by revenue, recent 10 orders
- `/admin/orders`: filter (status, date range, user email, product sku, amount range, ref_code search), bulk export CSV
- `/admin/orders/[id]`: chi tiết đơn, items, payment info, button "Mark as Paid" (manual fallback), webhook events log liên quan
- `/admin/products`: list/edit (from Phase 01)
- `/admin/users/[id]` (cập nhật): tab Orders + Reports + Quota history
- `/admin/webhook-events`: log webhooks (filter status: matched/unmatched/duplicate/error), search payload

### Non-functional
- Dashboard load <1s (cache metrics 60s)
- Order list filter <500ms với 10k orders
- CSV export streaming (no memory load) cho lượng lớn

## Architecture

### Backend endpoints

```
GET /admin/dashboard/metrics       → KPI summary (revenue, counts) - cached 60s
GET /admin/dashboard/revenue-chart → 30-day revenue series
GET /admin/dashboard/top-products  → top 5 products by revenue
GET /admin/orders                  → paginated + advanced filter
GET /admin/orders/{id}             → detail with webhook events
POST /admin/orders/{id}/mark-paid  → manual fulfill (from Phase 2)
GET /admin/orders/export.csv       → stream CSV
GET /admin/webhook-events          → paginated webhook log
GET /admin/users/{id}/orders       → user's orders
GET /admin/users/{id}/reports      → user's reports
```

### Backend structure

```
numerology-api/app/
├── routers/admin/
│   ├── dashboard.py       # NEW: metrics, charts
│   ├── orders.py          # NEW (already started phase 2)
│   ├── webhook_events.py  # NEW
│   └── users.py           # MODIFY: add /orders, /reports sub-endpoints
├── services/
│   ├── dashboard_service.py  # NEW: aggregate metrics queries
│   └── csv_export_service.py # NEW: stream CSV builder
└── schemas/
    ├── dashboard.py       # NEW
    └── admin_order.py     # NEW (advanced filter)
```

### Frontend structure

```
Numerology-Landing-Page/src/
├── pages/admin/
│   ├── index.tsx              # EXISTS: enhance dashboard
│   ├── orders/
│   │   ├── index.tsx          # NEW: list + filter + export
│   │   └── [id].tsx           # NEW: detail + actions
│   ├── webhook-events/
│   │   └── index.tsx          # NEW: log viewer
│   └── users/
│       └── [id].tsx           # MODIFY: add tabs
├── components/admin/
│   ├── dashboard-revenue-chart.tsx     # ENHANCE existing dashboard-charts.tsx
│   ├── dashboard-top-products.tsx      # NEW
│   ├── dashboard-kpi-grid.tsx          # NEW
│   ├── orders-filter-bar.tsx           # NEW
│   ├── orders-table-admin.tsx          # NEW (different from /my-account)
│   ├── order-detail-admin.tsx          # NEW
│   ├── mark-paid-button.tsx            # NEW (confirm dialog)
│   ├── webhook-event-row.tsx           # NEW (expandable JSON)
│   ├── csv-export-button.tsx           # NEW
│   └── user-orders-tab.tsx             # NEW
└── lib/
    └── admin-dashboard-api.ts          # NEW
```

## Related Code Files

### Create
- `numerology-api/app/routers/admin/dashboard.py`
- `numerology-api/app/routers/admin/orders.py` (extend Phase 2 partial)
- `numerology-api/app/routers/admin/webhook_events.py`
- `numerology-api/app/services/dashboard_service.py`
- `numerology-api/app/services/csv_export_service.py`
- `numerology-api/app/schemas/dashboard.py`
- `numerology-api/app/schemas/admin_order.py`
- `numerology-api/tests/test_admin_dashboard.py`
- `numerology-api/tests/test_admin_orders.py`
- `Numerology-Landing-Page/src/pages/admin/orders/index.tsx`
- `Numerology-Landing-Page/src/pages/admin/orders/[id].tsx`
- `Numerology-Landing-Page/src/pages/admin/webhook-events/index.tsx`
- `Numerology-Landing-Page/src/components/admin/dashboard-revenue-chart.tsx`
- `Numerology-Landing-Page/src/components/admin/dashboard-top-products.tsx`
- `Numerology-Landing-Page/src/components/admin/dashboard-kpi-grid.tsx`
- `Numerology-Landing-Page/src/components/admin/orders-filter-bar.tsx`
- `Numerology-Landing-Page/src/components/admin/orders-table-admin.tsx`
- `Numerology-Landing-Page/src/components/admin/order-detail-admin.tsx`
- `Numerology-Landing-Page/src/components/admin/mark-paid-button.tsx`
- `Numerology-Landing-Page/src/components/admin/webhook-event-row.tsx`
- `Numerology-Landing-Page/src/components/admin/csv-export-button.tsx`
- `Numerology-Landing-Page/src/components/admin/user-orders-tab.tsx`
- `Numerology-Landing-Page/src/lib/admin-dashboard-api.ts`

### Modify
- `numerology-api/app/main.py` — register dashboard, orders (admin), webhook_events routers
- `numerology-api/app/routers/admin/users.py` — add /admin/users/{id}/orders, /reports
- `Numerology-Landing-Page/src/pages/admin/index.tsx` — replace với new dashboard grid
- `Numerology-Landing-Page/src/components/admin/admin-nav-config.ts` — add Orders + Webhook Events menu
- `Numerology-Landing-Page/src/pages/admin/users/[id].tsx` — thêm tabs Orders/Reports/Quota

## Implementation Steps

1. **`dashboard_service.py`** — aggregate queries:
   - `get_revenue_today/week/month()` → SUM(orders.total_amount) WHERE status='paid' AND paid_at BETWEEN
   - `get_pending_orders_count()`
   - `get_revenue_chart_30d()` → GROUP BY DATE(paid_at) LIMIT 30
   - `get_top_products(limit=5)` → JOIN orders + items, GROUP BY product
   - Cache layer: in-memory TTL 60s (functools.lru_cache với timestamp key hoặc cachetools)
2. **Router `/admin/dashboard/*`** — 3 endpoints
3. **`csv_export_service.py`** — async generator streaming CSV rows
4. **Router `/admin/orders`** — paginated với advanced filter (status, date, user_email LIKE, product_sku, amount range)
5. **Router `/admin/orders/{id}`** — eager load items + webhook_events
6. **Router `/admin/orders/export.csv`** — StreamingResponse với csv_export_service
7. **Router `/admin/webhook-events`** — paginated, filter by status, search payload JSONB (`raw_payload @> '{"content":"..."}'`)
8. **Modify `/admin/users/{id}`** — return user + recent 10 orders + recent 10 reports + quota total
9. **Tests** — dashboard metrics accuracy, orders filter correctness, CSV export with 1000 rows, webhook events search
10. **Frontend dashboard enhance** — replace index.tsx với new KPI grid + chart + top products + recent orders. Reuse existing `dashboard-stat-card.tsx`
11. **Frontend orders pages** — filter bar (date pickers, select status, search input), table với sortable columns, pagination
12. **Frontend order detail** — sections: Order Info, Items, Payment, Webhook Events Log (expandable JSON), action buttons
13. **Frontend mark-paid-button** — confirm dialog: "Xác nhận đã nhận tiền bằng cách khác?" + lý do textarea (optional)
14. **Frontend csv-export-button** — trigger window.open URL với current filter params
15. **Frontend webhook-events page** — log viewer với expandable rows
16. **Frontend admin-nav-config** — thêm 2 menu items, update sidebar
17. **Frontend user detail tabs** — Tabs UI với Orders / Reports / Quota History
18. **Manual test** — tạo data mẫu 50 orders → verify dashboard số đúng, filter hoạt động, export CSV mở Excel OK

## Todo List

- [ ] M1. dashboard_service với caching
- [ ] M2. csv_export_service streaming
- [ ] M3. Router admin/dashboard 3 endpoints
- [ ] M4. Router admin/orders với filter + export
- [ ] M5. Router admin/webhook-events
- [ ] M6. Router admin/users/{id} mở rộng tabs data
- [ ] M7. Tests admin_dashboard, admin_orders
- [ ] M8. Frontend dashboard page enhanced
- [ ] M9. Frontend orders list + filter bar
- [ ] M10. Frontend order detail page
- [ ] M11. Frontend mark-paid button + dialog
- [ ] M12. Frontend csv-export button
- [ ] M13. Frontend webhook-events page
- [ ] M14. Frontend user detail tabs
- [ ] M15. Admin nav config update
- [ ] M16. Manual test với 50 orders sample

## Success Criteria

- Dashboard load <1s, cache hit khi reload trong 60s
- Filter orders by 5 criteria cùng lúc trả kết quả đúng
- Export CSV 1000 orders < 3s, file mở Excel UTF-8 đúng tiếng Việt
- Admin click "Mark as Paid" → order paid + fulfillment chạy + UI refresh
- Webhook events page search được "NSQ-A1B2" trong content JSON
- User detail page hiện tab Orders với count + revenue total

## Risk Assessment

| Risk | Mức | Mitigation |
|------|-----|-----------|
| Dashboard query chậm khi orders > 100k | Cao | Index trên `orders(status, paid_at)`; materialized view sau nếu cần; cache 60s |
| CSV export load full vào memory crash | Cao | StreamingResponse + async generator yield từng row |
| Webhook events JSONB search chậm | TB | GIN index trên `raw_payload`; limit search trong 30 ngày gần nhất |
| Cache stale → admin thấy số cũ | Thấp | TTL 60s acceptable; admin có button "Refresh" force |
| Filter date range UTC vs local timezone (Asia/Bangkok) | TB | Backend nhận ISO string + timezone, convert UTC trước query; document rõ |
| Mark-paid abuse (admin fake) | Thấp | Log mọi mark-paid với admin_id + timestamp + reason; Phase 2 audit log formal |

## Security Considerations

- Tất cả `/admin/*` require `get_current_superuser`
- CSV export filter same as list (không leak data ngoài scope filter)
- Webhook payload có thể chứa info nhạy cảm → mask account_number ở UI (chỉ hiện 4 số cuối)
- Rate limit `/admin/dashboard/metrics` 10 req/phút/admin (tránh DoS internal)
- Audit log lightweight: log mọi admin POST/PUT/DELETE vào file (Phase 6 sẽ formal hơn)

## Next Steps
- Parallel với Phase 03, 05
- Phase 06 sẽ thêm cron tự gửi daily report email cho admin
