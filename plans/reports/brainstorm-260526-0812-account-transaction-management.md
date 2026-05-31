# Brainstorm Report — Account & Transaction Management

**Date:** 2026-05-26
**Project:** Numerology Platform (FastAPI + Next.js)
**Scope:** Production-ready (1-2 tháng) — user-facing + admin + auto giao dịch SePay
**Author:** Solution Brainstormer (Claude)

---

## 1. Problem Statement

Hiện tại platform đã có infra auth/payment cơ bản (users, user_payments, user_packages, banks) nhưng:
- **Manual:** admin duyệt từng giao dịch bằng tay → tốn nhân lực, user phải chờ.
- **Thiếu trang my-account:** user không có nơi xem lịch sử, quota, báo cáo đã mua.
- **Mô hình hẹp:** chỉ bán gói quota; chưa upsell báo cáo chuyên sâu (premium pay-per-report).
- **Không notification:** user không biết đơn được duyệt hay sắp hết quota.

**Mục tiêu:** Production-ready full-stack account + transaction system, auto via SePay, hybrid pricing (gói + báo cáo lẻ), kèm email transactional.

---

## 2. Decisions Locked (qua brainstorm)

| Hạng mục | Lựa chọn |
|----------|---------|
| Phạm vi | User-facing + Admin + Auto SePay |
| Mô hình giao dịch | Hybrid: gói quota + báo cáo lẻ premium |
| Cổng thanh toán | SePay (VietQR auto, webhook bank-event) |
| SePay matching | Reference code trong nội dung chuyển khoản (vd `NSQ-A1B2C3`) |
| Báo cáo lẻ | Tích hợp lại 22 content tables hiện có + thêm 3-5 template chuyên sâu |
| Notification | Email transactional (đăng ký, mua thành công, hóa đơn, sắp hết quota) |
| Refund/Audit log | Skip Phase 1 → đưa vào Phase 2 |

---

## 3. Kiến trúc tổng quan

```
┌─────────────────────────────────────────────────────────────────┐
│ User Browser (Next.js)                                          │
│  ├── /my-account/* (dashboard, lịch sử, quota, reports)         │
│  ├── /shop (catalogue gói + báo cáo lẻ)                         │
│  └── /checkout/[orderId] (QR + auto-poll status)                │
└──────────────────────┬──────────────────────────────────────────┘
                       │ REST + Bearer JWT
┌──────────────────────▼──────────────────────────────────────────┐
│ FastAPI Backend                                                 │
│  ├── /orders (create order → ref_code + SePay QR URL)          │
│  ├── /orders/{id}/status (poll thanh toán)                      │
│  ├── /my/* (transactions, reports, quota)                       │
│  ├── /admin/* (revenue dashboard, manual mark-paid, filter)     │
│  └── /webhooks/sepay (HMAC verify → match ref_code → fulfill)   │
│                                                                 │
│  Services:                                                       │
│  ├── order_service: tạo đơn, sinh ref_code unique               │
│  ├── sepay_service: parse webhook, verify, idempotent fulfill   │
│  ├── fulfillment_service: cộng quota / cấp user_report          │
│  ├── email_service: SMTP/Resend, template Jinja2                │
│  └── report_service: render PDF báo cáo lẻ theo template        │
└──────────────────────┬──────────────────────────────────────────┘
                       │ webhook
┌──────────────────────▼──────────────────────────────────────────┐
│ SePay (cổng VietQR)                                             │
│  ├── User quét QR → CK ngân hàng → biến động số dư             │
│  └── POST webhook → backend (kèm content, amount, ref)          │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. Data Model Changes

### Bảng mới
```sql
-- Catalogue: định nghĩa SKU bán (gói + báo cáo lẻ + combo)
products (
  id, sku, type ENUM('package','report','combo'), name, slug,
  price, currency='VND',
  -- nếu type=package: quota, renewal_days
  quota, renewal_days,
  -- nếu type=report: template, content_codes JSON (vd ['souls_number','balance_number'])
  template_name, content_codes,
  -- combo: tham chiếu products khác qua product_items
  is_active, sort_order, created_at, updated_at
)
product_items (id, combo_id FK products, item_id FK products, qty)

-- Đơn hàng (thay/bọc user_payments hiện tại)
orders (
  id, user_id FK, ref_code U INDEX,         -- ref_code unique → match webhook
  total_amount, currency='VND',
  status ENUM('pending','paid','cancelled','expired','failed') INDEX,
  payment_method='sepay',
  expires_at,                                -- pending 30 phút auto-expire
  paid_at, sepay_tx_id INDEX,                -- idempotency key từ SePay
  created_at, updated_at
)
order_items (
  id, order_id FK, product_id FK,
  qty, unit_price, snapshot_name           -- snapshot giá tại thời điểm mua
)

-- Báo cáo lẻ đã mua (vĩnh viễn truy cập)
user_reports (
  id, user_id FK, order_id FK, product_id FK,
  pdf_path, generated_at, input_payload JSON,  -- name/birthday/phone đầu vào
  download_count, last_downloaded_at
)

-- Webhook events log (debug + idempotency)
webhook_events (
  id, source='sepay', sepay_tx_id U INDEX,
  raw_payload JSONB, processed_at, order_id FK NULL,
  status ENUM('received','matched','unmatched','duplicate','error'),
  error_message
)

-- Email outbox (retry-safe)
email_outbox (
  id, to_email, template, payload JSONB,
  status ENUM('pending','sent','failed'), attempts,
  sent_at, error_message, created_at
)
```

### Bảng giữ nguyên (refactor nhẹ)
- `users`, `user_profiles`: thêm field `quota` đã có → tiếp tục dùng
- `user_packages`: cộng từ `orders` khi paid → giữ logic expires_at hiện có
- `user_payments`: **deprecate dần** (migrate sang `orders`) hoặc giữ làm view legacy
- `packages`, `banks`: dùng làm data source ban đầu cho seed `products`

---

## 5. Phasing (8 tuần)

### Phase 1: Foundation — Products & Orders (Tuần 1-2)
**Backend:**
- Migration: tạo `products`, `orders`, `order_items`, `user_reports`, `webhook_events`, `email_outbox`
- Models + schemas + CRUD endpoints `/products` (public), `/admin/products` (CMS)
- Seed: migrate `packages` cũ → `products(type=package)` + tạo 3-5 `products(type=report)` premium
- Service `order_service.create_order(user_id, items[])` → sinh `ref_code` (NSQ + 8-char base32)

**Frontend:**
- Trang `/shop`: catalogue tabs (Gói | Báo cáo lẻ | Combo), card sản phẩm
- Trang `/checkout/[orderId]`: hiện QR (SePay generator), reference code, hướng dẫn CK, auto-poll status mỗi 3s

**DoD:** User tạo được đơn, thấy QR + ref_code, status pending.

---

### Phase 2: SePay Integration + Fulfillment (Tuần 3)
**Backend:**
- Endpoint `POST /webhooks/sepay`:
  - Verify API key (header `Authorization: Apikey <SEPAY_KEY>`)
  - Parse payload → extract `content`, `transferAmount`, `id` (sepay_tx_id), `transferType=in`
  - Idempotency: `webhook_events.sepay_tx_id` UNIQUE → skip duplicate
  - Regex extract `ref_code` từ content → lookup `orders.ref_code`
  - Validate `amount` khớp `total_amount` (±1k tolerance cho rounding)
  - Atomic transaction: `orders.status='paid'` + `sepay_tx_id` + `paid_at`
  - Call `fulfillment_service.fulfill(order_id)`
- Service `fulfillment_service`:
  - Cho mỗi `order_item`:
    - `type=package` → upsert `user_packages` (cộng quota + expires_at)
    - `type=report` → render PDF (Jinja2 template + content_codes pull từ 22 tables) → tạo `user_reports`
    - `type=combo` → expand → recursion
  - Enqueue email "Mua thành công"

**Frontend:**
- Trang checkout: detect status=paid → redirect `/my-account/reports/[id]` (báo cáo lẻ) hoặc `/my-account` (gói)

**DoD:** End-to-end test: tạo đơn → CK thật → webhook → quota tăng / báo cáo xuất hiện.

---

### Phase 3: User Account UI (Tuần 4)
**Frontend `/my-account/*`:**
- `/my-account` — Dashboard: avatar, quota còn lại, gói active, link nhanh
- `/my-account/profile` — Edit name/birthday/gender/address/phone, đổi mật khẩu
- `/my-account/orders` — Lịch sử giao dịch (filter status, search ref_code, paginate)
- `/my-account/orders/[id]` — Chi tiết đơn (items, ref_code, hóa đơn PDF download)
- `/my-account/reports` — Thư viện báo cáo lẻ đã mua (download lại bất kỳ lúc nào)
- `/my-account/downloads` — Lịch sử PDF đã tải (từ quota gói)

**Backend `/my/*`:** read-only endpoints filter `user_id=current_user.id`.

**DoD:** User self-service đầy đủ, không cần admin can thiệp use case thường.

---

### Phase 4: Admin Dashboard (Tuần 5)
**Frontend `/admin/*` mới:**
- `/admin/dashboard` — KPI cards (doanh thu hôm nay/tuần/tháng, đơn pending, MRR ước tính, top products), biểu đồ line revenue 30 ngày
- `/admin/orders` — Filter (status, date range, user, sku, amount range), bulk export CSV
- `/admin/orders/[id]` — Chi tiết, button **"Đánh dấu đã thanh toán thủ công"** (fallback khi webhook miss)
- `/admin/products` — CRUD products + items + active toggle, drag-drop sort_order
- `/admin/users/[id]` — Tab Orders + Reports + Quota (nâng cấp trang user hiện có)

**Backend:** `/admin/dashboard/metrics`, `/admin/orders` (enhanced filter), `/admin/orders/{id}/mark-paid` (manual fulfill).

**DoD:** Admin có overview doanh thu real-time + xử lý exception nhanh.

---

### Phase 5: Email Transactional (Tuần 6)
**Backend:**
- Provider: **Resend** (recommend — DX tốt, free 100/day, API đơn giản) hoặc SMTP Gmail/Brevo
- Worker: `email_dispatcher` cron 1 phút quét `email_outbox.status=pending` → gửi → retry với exponential backoff (max 5 lần)
- Templates Jinja2 trong `app/templates/emails/`:
  - `welcome.html` — đăng ký xong
  - `order_paid.html` — mua gói/báo cáo thành công, kèm link
  - `order_expired.html` — đơn pending quá 30 phút → auto cancel + email
  - `quota_low.html` — quota < 20%
  - `quota_expired.html` — gói hết hạn
  - `password_reset.html` — (giữ logic hiện có, chuẩn hóa template)
- Trigger points: `auth_service` (register), `fulfillment_service` (paid), `order_service` (expire), `numerology_paid` (sau khi decrement quota check threshold)

**Frontend:**
- Trang `/my-account/settings/notifications` — toggle bật/tắt từng loại email (lưu vào `user_profiles.notification_prefs JSONB`)

**DoD:** Email gửi đúng thời điểm, không spam, có unsubscribe link.

---

### Phase 6: Hardening + Background Jobs (Tuần 7)
- **Cron jobs** (APScheduler hoặc systemd timer):
  - `expire_pending_orders` — mỗi 5 phút, set `orders.status='expired'` cho pending quá `expires_at`
  - `check_quota_warnings` — mỗi giờ, gửi email khi quota_remaining/quota_total < 20%
  - `check_package_expiry` — mỗi ngày 7AM, gửi email khi `user_packages.expires_at` < 3 ngày
- **Rate limiting** webhook endpoint (slowapi 100req/min/IP, bypass cho whitelist IP SePay)
- **Monitoring:** thêm `/health` chi tiết (db + sepay reachable), Sentry integration cho exception
- **Security:** review CSRF (FastAPI mostly stateless OK), SQL injection (SQLAlchemy ORM OK), webhook signature must-have

---

### Phase 7: Testing + Docs + Deploy (Tuần 8)
- Pytest: order_service, sepay webhook (mock payloads), fulfillment idempotency, email outbox retry
- E2E (Cypress hiện có): flow mua gói + mua báo cáo lẻ end-to-end
- Load test webhook (k6): 100 concurrent webhook events, đảm bảo no double-fulfillment
- Docs: cập nhật `docs/system-architecture.md`, viết runbook `docs/sepay-integration-runbook.md`
- Deploy: migration zero-downtime, env var mới (`SEPAY_API_KEY`, `RESEND_API_KEY`)

---

## 6. Key Technical Decisions & Rationale

| Quyết định | Lý do |
|-----------|-------|
| **`orders` thay vì mở rộng `user_payments`** | Tách rõ: payment chỉ là 1 phương thức; order có items, snapshot price, refund-ready (phase 2). Migration cũ → mới bằng view legacy |
| **`ref_code` 8 char base32 + prefix `NSQ`** | Đủ unique (32^8 = 1T tổ hợp), dễ đọc khi user gõ tay, regex `NSQ[A-Z0-9]{8}` clear |
| **Idempotency qua `sepay_tx_id UNIQUE`** | SePay có thể retry webhook → tránh cộng quota 2 lần. DB constraint > app-level check |
| **`webhook_events` log đầy đủ payload** | Debug khi user khiếu nại "tôi CK rồi sao chưa thấy" → tra raw payload nhanh |
| **`email_outbox` thay vì gửi sync** | SMTP fail không nên block API response; retry tự động; audit-friendly |
| **`user_reports` permanent access** | Đã mua = sở hữu vĩnh viễn → tăng giá trị cảm nhận, không cần tải lại tốn tiền |
| **Báo cáo lẻ tái dùng 22 content tables** | DRY tối đa: nội dung đã có, chỉ thêm template + chọn content_codes phù hợp theme |
| **Frontend poll 3s thay vì WebSocket** | YAGNI: webhook trung bình về <10s, polling đơn giản, không cần infra realtime |

---

## 7. Risks & Mitigations

| Rủi ro | Mức | Mitigation |
|--------|-----|-----------|
| User CK sai nội dung (thiếu ref_code) | Cao | Webhook log `unmatched` → admin UI có tab "Giao dịch không khớp" để gán thủ công vào order |
| SePay webhook bị down/delay | TB | Cron job `reconcile_sepay` (tuần 7) gọi SePay API list-transactions, đối soát các order pending |
| User thấy QR nhưng app crash trước khi paid | Thấp | `orders.expires_at` 30 phút auto-cancel; user tạo lại đơn mới |
| Email rơi vào spam | TB | Setup SPF/DKIM/DMARC; dùng Resend với domain verified; tránh keyword spam trong subject |
| Race condition khi 2 webhook gần nhau | TB | `orders` status transition wrapped in `SELECT FOR UPDATE`; UNIQUE constraint trên `sepay_tx_id` |
| Migration `user_payments` → `orders` mất data | Cao | Script migrate riêng, giữ song song 2 tuần, có rollback plan; test trên staging trước |
| Báo cáo PDF render lỗi sau khi đã thu tiền | Cao | Tách "đã thanh toán" và "đã render": nếu render fail, queue retry; user vẫn thấy "Đang xử lý"; admin notify |

---

## 8. Success Metrics

**Functional:**
- ≥95% giao dịch auto-fulfill trong <30s sau khi SePay webhook về
- 0 case double-fulfillment trong 1 tháng đầu
- ≥80% user mua thành công không cần liên hệ support

**Business:**
- Doanh thu báo cáo lẻ ≥ 30% tổng doanh thu sau 2 tháng (nếu không → cần review pricing/UX shop)
- Tỉ lệ đơn pending → paid ≥ 70%
- Email mở rate ≥ 40% (order_paid), ≥ 25% (quota_low)

**Technical:**
- Webhook P99 latency < 500ms
- Test coverage ≥ 80% cho `order_service` + `fulfillment_service` + `sepay_service`
- 0 leak credentials trong logs

---

## 9. Out-of-scope (Phase 2 / Future)

- Refund flow (admin hoàn quota, ghi lý do, có thể tạo SePay reverse-transfer)
- Audit log mọi mutation admin (ai sửa gì, khi nào, IP)
- Invoice PDF chính thống (có VAT, mã số thuế) — nếu doanh nghiệp KYC
- Multi-currency / Stripe cho user quốc tế
- Zalo ZNS / SMS OTP notification
- Coupon / voucher / referral
- Subscription auto-renew (chỉ làm khi có cổng thanh toán recurring như VNPay token)
- Admin role-based permissions (hiện tại chỉ binary superuser/regular)

---

## 10. Next Steps

1. **User review** report này, confirm hoặc điều chỉnh decision nào
2. **Tạo detailed implementation plan** qua `/ck:plan` (sẽ tách 7 phase trên thành plan dir + 7 phase files, mỗi phase chi tiết todo + file paths)
3. **Đăng ký SePay account** + tạo bank link (cần làm song song khi dev Phase 1-2)
4. **Đăng ký Resend account** + verify domain `nhansinhquan.vn` (DNS propagation mất 24-48h, làm sớm)
5. **Wireframe** trang `/shop`, `/checkout`, `/my-account` (có thể dùng `ck:ui-ux-pro-max` skill)

---

## 11. Final Configuration (resolved)

### Catalogue sản phẩm

**Gói quota** (giữ nguyên hiện tại, seed lại vào `products`):
- Free / Basic / Premium (price + quota + renewal_days như cũ)

**Báo cáo lẻ premium** (3 SKU, content_codes pull từ 22 content tables):

| SKU | Tên | Giá gợi ý | Pages | content_codes chính |
|-----|-----|----------|-------|---------------------|
| `report-overview` | Báo cáo Tổng quan Thần số học | 99.000₫ | 30-50 | `main_number`, `mission_number`, `souls_number`, `personality`, `mature_number`, `birthday_chart`, `name_chart`, `peak_life`, `stages_of_life`, `personal_year_number` (full) |
| `report-love` | Báo cáo Tình duyên & Hôn nhân | 79.000₫ | 15-25 | `souls_number`, `balance_number`, `personality`, `attitude_number`, `personal_year_number` (theme love) |
| `report-career` | Báo cáo Sự nghiệp & Tài chính | 79.000₫ | 15-25 | `mission_number`, `execution_number`, `mature_number`, `stages_of_life`, `peak_life`, `personal_year_number` (theme career) |

**Lead magnet** (free signup gift):
- SKU `report-mini-free`: `type=report`, `price=0`, auto-grant khi user verify email đăng ký
- 5-7 trang rút gọn từ `report-overview` (chỉ main_number + mission + 1-2 trang gợi mở)
- Cấp 1 lần/user (check unique `user_reports.product_id + user_id`)

### Email infrastructure
- **Provider:** Resend
- **Domain verified:** `nhansinhquan.vn` (cần thêm SPF + DKIM TXT records, plan sẽ document cụ thể)
- **From:** `no-reply@nhansinhquan.vn`, reply-to `support@nhansinhquan.vn`

### Payment infrastructure
- **SePay account:** đã có sẵn → API key inject qua env `SEPAY_API_KEY`
- **Bank account:** 1 STK duy nhất nhận tiền (tên ngân hàng + số tài khoản qua env hoặc bảng `banks`)
- **Webhook endpoint:** `POST /api/v1/webhooks/sepay` (whitelist IP SePay + verify Apikey header)
- **Reference code format:** `NSQ-{8chars base32}` (vd `NSQ-A1B2C3D4`), regex match trong `content` field webhook

---

## 12. Next Steps

1. **Chạy `/ck:plan`** với context report này → sinh plan dir `260526-0812-account-transaction-management/` + 7 phase files chi tiết
2. **Song song dev Phase 1-2:**
   - Bạn cung cấp: SePay API key, STK bank, tên người thụ hưởng
   - DevOps: thêm DNS records cho Resend (TXT _resend, DKIM, DMARC) — propagate 24-48h nên làm sớm
3. **Sau khi plan xong:** delegate `planner` → `fullstack-developer` triển khai từng phase
