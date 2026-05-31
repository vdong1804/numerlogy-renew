# Phase 02 — SePay Integration + Fulfillment

## Context Links
- [Plan overview](./plan.md)
- [Phase 01](./phase-01-foundation-products-orders.md)
- SePay docs: https://docs.sepay.vn/ (user verify version mới nhất)

## Overview
- **Priority:** P0 (core revenue mechanism)
- **Status:** pending
- **Duration:** Tuần 3 (5 ngày dev)
- **Description:** Tích hợp SePay webhook để auto duyệt giao dịch. Khi user CK đủ tiền + đúng ref_code → webhook về backend → match order → fulfill (cộng quota cho gói, render PDF cho báo cáo). Idempotent + secure.

## Key Insights
- SePay webhook gửi POST với header `Authorization: Apikey <key>` + body JSON có fields: `id`, `gateway`, `transactionDate`, `accountNumber`, `code`, `content`, `transferType`, `transferAmount`, `referenceCode`, `description`
- Reference code parse từ `content` field (regex `NSQ-[A-Z0-9]{8}`)
- Idempotency key = SePay `id` (UNIQUE trong `webhook_events.sepay_tx_id`)
- Render PDF báo cáo lẻ → reuse `app/utils/pdf.py` + Jinja2 templates mới
- Lead magnet `report-mini-free` trigger ngay sau email verify (KHÔNG qua SePay)

## Requirements

### Functional
- POST `/api/v1/webhooks/sepay` nhận webhook, verify API key
- Parse content → extract ref_code → match order pending
- Validate amount khớp (±1k tolerance)
- Atomic transaction: update order paid + fulfill
- Idempotent: webhook gọi nhiều lần cho cùng tx_id → no double fulfill
- Render PDF báo cáo lẻ theo template + content_codes
- Auto-grant lead magnet khi user mới đăng ký
- Manual "mark as paid" cho admin (fallback khi webhook miss)

### Non-functional
- Webhook P99 <500ms
- Concurrent webhook safe (race condition prevention)
- Log mọi webhook payload (debug khiếu nại)

## Architecture

### Webhook flow

```
SePay → POST /api/v1/webhooks/sepay
        │
        ├─ Verify Apikey header (env SEPAY_API_KEY)
        ├─ Insert webhook_events (status=received)
        ├─ INSERT ON CONFLICT(sepay_tx_id) DO NOTHING → if duplicate, return 200 + log
        ├─ Parse ref_code from content (regex)
        │   └─ no match → status=unmatched, return 200 (don't error, SePay retries)
        ├─ Lookup order BY ref_code WHERE status='pending' FOR UPDATE
        │   └─ not found / not pending → status=unmatched, return 200
        ├─ Validate amount (|paid - expected| <= 1000 VND)
        │   └─ mismatch → status=error, alert admin, return 200
        ├─ Update order: status='paid', sepay_tx_id, paid_at=NOW
        ├─ fulfillment_service.fulfill(order_id)
        │   ├─ For each order_item:
        │   │   ├─ type='package' → upsert user_packages (quota++, expires_at=NOW+renewal_days)
        │   │   ├─ type='report'  → render PDF (Jinja2 + content_codes) → insert user_reports
        │   │   └─ type='combo'   → recurse on combo items
        │   └─ enqueue email_outbox(template='order_paid', user_id, order_id)
        ├─ Update webhook_events: status=matched, order_id
        └─ Return 200 OK
```

### Backend structure

```
numerology-api/app/
├── db/models/
│   └── webhook_event.py    # NEW
├── schemas/
│   └── webhook.py          # NEW: SePayWebhookPayload
├── services/
│   ├── sepay_service.py    # NEW: verify, parse, process_webhook
│   └── fulfillment_service.py # NEW: fulfill_order, fulfill_item
├── routers/
│   ├── webhooks.py         # NEW: POST /webhooks/sepay
│   └── admin/
│       └── orders.py       # NEW: POST /admin/orders/{id}/mark-paid
├── templates/
│   └── reports/
│       ├── report-overview.html  # NEW: Jinja2 template báo cáo Tổng quan
│       ├── report-love.html      # NEW: báo cáo Tình duyên
│       ├── report-career.html    # NEW: báo cáo Sự nghiệp
│       └── report-mini-free.html # NEW: lead magnet 5-7 trang
└── alembic/versions/
    └── 0005_webhook_events.py    # NEW
```

### Frontend updates
- `/check-out/[orderId]` poll status detect `paid` → redirect:
  - Gói → `/my-account` (phase 3)
  - Báo cáo lẻ → `/my-account/reports/[reportId]` để download
- Admin order detail page: button "Đánh dấu đã thanh toán" (calls mark-paid endpoint)

## Related Code Files

### Create
- `numerology-api/alembic/versions/0005_webhook_events.py`
- `numerology-api/app/db/models/webhook_event.py`
- `numerology-api/app/schemas/webhook.py`
- `numerology-api/app/services/sepay_service.py`
- `numerology-api/app/services/fulfillment_service.py`
- `numerology-api/app/routers/webhooks.py`
- `numerology-api/app/routers/admin/orders.py`
- `numerology-api/app/templates/reports/report-overview.html`
- `numerology-api/app/templates/reports/report-love.html`
- `numerology-api/app/templates/reports/report-career.html`
- `numerology-api/app/templates/reports/report-mini-free.html`
- `numerology-api/tests/test_sepay_webhook.py`
- `numerology-api/tests/test_fulfillment_service.py`

### Modify
- `numerology-api/app/main.py` — register webhooks router, admin/orders router
- `numerology-api/app/db/models/__init__.py` — export WebhookEvent
- `numerology-api/app/config.py` — add `SEPAY_API_KEY`, `SEPAY_WEBHOOK_IP_WHITELIST`
- `numerology-api/app/routers/auth.py` — call grant lead magnet sau khi register success
- `numerology-api/app/services/user_service.py` — helper `grant_free_report(user_id)`
- `numerology-api/app/services/numerology_context.py` — extract content fetching logic để reuse cho report templates
- `numerology-api/.env.example` — thêm SEPAY env vars
- `Numerology-Landing-Page/src/components/checkout/order-status-poller.tsx` — handle paid redirect

## Implementation Steps

1. **Migration 0005** — `webhook_events` table với UNIQUE(sepay_tx_id), index status
2. **Model `WebhookEvent`** + export
3. **Config** — add SEPAY_API_KEY, SEPAY_WEBHOOK_IP_WHITELIST (optional, comma-separated)
4. **Pydantic `SePayWebhookPayload`** — match SePay payload schema
5. **`sepay_service.parse_ref_code(content) -> Optional[str]`** — regex `NSQ-[A-Z0-9]{8}`
6. **`sepay_service.verify_apikey(header) -> bool`** — constant-time compare
7. **`sepay_service.process_webhook(payload) -> WebhookEvent`** — main entry, handle idempotency, lock order FOR UPDATE, call fulfillment
8. **`fulfillment_service.fulfill_order(db, order)`** — iterate items, dispatch by type
9. **`fulfillment_service._fulfill_package(db, user, package_product)`** — upsert user_packages
10. **`fulfillment_service._fulfill_report(db, user, report_product, order)`** — call `_render_report_pdf`, insert user_reports
11. **`fulfillment_service._render_report_pdf(template_name, content_codes, input_payload) -> str`** — fetch content from 22 tables theo codes, render Jinja2, call wkhtmltopdf, lưu file → return path
12. **Router `/webhooks/sepay`** — call sepay_service, return 200 always (except auth fail = 401)
13. **Router `/admin/orders/{id}/mark-paid`** — admin manual fulfill (skip SePay, mark `sepay_tx_id='MANUAL-{admin_id}'`)
14. **Templates Jinja2** — 4 báo cáo templates, layout chung extend `base_report.html`, dùng partial từ `invoice.html` cũ
15. **Lead magnet grant** — modify `auth.py` register handler: sau khi user create, call `grant_free_report(user_id)` → insert user_reports với product_id của `report-mini-free`, render PDF luôn
16. **Tests:**
    - `test_sepay_webhook.py`: valid payload, invalid apikey, duplicate tx_id, unmatched ref, amount mismatch, race condition (2 webhooks concurrent)
    - `test_fulfillment_service.py`: package fulfill, report fulfill, combo fulfill, idempotency
17. **Frontend poller update** — sau khi detect paid + type=report → redirect tải PDF
18. **Manual E2E** — tạo đơn, mock SePay POST với httpie/curl, verify quota tăng / PDF tạo

## Todo List

- [ ] M1. Migration 0005 webhook_events + run
- [ ] M2. Model WebhookEvent + export
- [ ] M3. Config SEPAY_API_KEY + .env.example update
- [ ] M4. Schemas SePayWebhookPayload
- [ ] M5. sepay_service: parse_ref_code, verify_apikey, process_webhook
- [ ] M6. fulfillment_service: fulfill_order + dispatch by type
- [ ] M7. fulfillment_service: _fulfill_package, _fulfill_report (+ _render_report_pdf)
- [ ] M8. Router /webhooks/sepay + register
- [ ] M9. Router /admin/orders/{id}/mark-paid + register
- [ ] M10. Templates Jinja2: report-overview, report-love, report-career, report-mini-free, base_report
- [ ] M11. Lead magnet grant tại auth register handler
- [ ] M12. Tests test_sepay_webhook.py (≥10 cases)
- [ ] M13. Tests test_fulfillment_service.py (≥6 cases)
- [ ] M14. Frontend order-status-poller: handle paid redirect by type
- [ ] M15. E2E manual: mock webhook → verify fulfill
- [ ] M16. Documentation: viết runbook test SePay sandbox

## Success Criteria

- Webhook với valid payload → order paid + fulfill <500ms
- Duplicate webhook (cùng sepay_tx_id) → 200 OK, không double fulfill
- Webhook không match ref_code → 200 OK, log `unmatched`, admin xem được
- Webhook sai apikey → 401
- 2 webhook concurrent cùng order → chỉ 1 thành công (FOR UPDATE lock)
- Test coverage ≥85% cho `sepay_service` + `fulfillment_service`
- Báo cáo PDF render đúng template với content_codes filter
- User register mới → tự động có lead magnet PDF trong user_reports
- Admin click "Đánh dấu đã thanh toán" → order paid + fulfill thành công

## Risk Assessment

| Risk | Mức | Mitigation |
|------|-----|-----------|
| Race condition: 2 webhook đến cùng lúc → double fulfill | Cao | `SELECT ... FOR UPDATE` order row + UNIQUE constraint `sepay_tx_id` |
| SePay webhook không gửi (network/down) → user CK xong mà không được fulfill | Cao | Phase 6 cron reconcile gọi SePay API list-transactions; Phase 2 fallback: admin mark-paid manual |
| Wkhtmltopdf hang / fail → user trả tiền mà không có PDF | Cao | Tách "paid" và "rendered": order paid trước, render async với retry; nếu fail → admin manual re-render |
| Lead magnet PDF render khi register làm chậm signup | TB | Render async (background task FastAPI BackgroundTasks), không block response register |
| Content codes thiếu trong 22 tables → template crash | Cao | Validate seed_products: check tất cả content_codes tồn tại; template dùng `{{ content.get(code, default) }}` |
| SePay đổi schema webhook | TB | Schema Pydantic validation rõ, log raw payload; có alert khi parse fail |
| Ref code regex match nhầm trong content phức tạp | TB | Regex strict: `\bNSQ-[A-Z0-9]{8}\b` với word boundary; test với 20+ content samples |

## Security Considerations

- Webhook endpoint MUST verify Apikey header (constant-time compare, prevent timing attack)
- Optional: whitelist IP SePay (env `SEPAY_WEBHOOK_IP_WHITELIST`)
- Webhook KHÔNG yêu cầu CSRF token (stateless, machine-to-machine)
- KHÔNG log full Apikey trong webhook_events (chỉ hash 8 ký tự đầu)
- Admin mark-paid endpoint require `get_current_superuser` + log admin_id vào audit (phase 2 sẽ formal log)
- PDF path lưu absolute → router serve qua `/my/reports/{id}/download` với check ownership, KHÔNG serve trực tiếp /media

## Next Steps
- Sau DoD pass → Phase 03 (User Account UI) + 04 (Admin) + 05 (Email) có thể chạy song song
- Cung cấp: SePay sandbox để test (hoặc dùng production với test order amount nhỏ)
