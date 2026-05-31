# Phase 01 — Foundation: Products & Orders

## Context Links
- [Plan overview](./plan.md)
- [Brainstorm report](../reports/brainstorm-260526-0812-account-transaction-management.md)
- Codebase: `numerology-api/app/db/models/`, `Numerology-Landing-Page/src/pages/`

## Overview
- **Priority:** P0 (blocking for all subsequent phases)
- **Status:** pending
- **Duration:** Tuần 1-2 (10 ngày dev)
- **Description:** Tạo data model mới (products, orders, items, user_reports), CRUD endpoints, seed catalogue, shop page UI, checkout page với QR placeholder. End-to-end "tạo đơn → thấy QR + ref_code" hoạt động (chưa cần SePay thật).

## Key Insights
- Hiện có `packages`, `user_payments`, `user_packages` — sẽ migrate dần sang `products` + `orders`
- 22 numerology content tables đã có → báo cáo lẻ chỉ cần thêm template + chọn content_codes, không tạo content mới
- `payment_service.py` đã tồn tại → refactor không tạo file mới
- Frontend đã có `check-out/index.tsx` → mở rộng thành `/check-out/[orderId].tsx`

## Requirements

### Functional
- User browse catalogue tại `/shop`, filter theo type (gói / báo cáo / combo)
- User tạo order với 1+ items → backend sinh `ref_code` unique
- Checkout page hiện thông tin CK (STK + amount + ref_code), poll status mỗi 3s
- Order auto-expire sau 30 phút nếu chưa paid
- Admin CRUD `/admin/products` (toggle active, sort order, edit price)

### Non-functional
- `ref_code` generation collision-free (UNIQUE constraint + retry 3 lần nếu trùng)
- Order create endpoint <200ms (no external call)
- Migration backward-compat: bảng cũ `user_payments` vẫn đọc được

## Architecture

### Data Model (Alembic migration 0004)

```python
# products
id: UUID PK
sku: str(64) UNIQUE INDEX
type: enum('package','report','combo')
name: str(255)
slug: str(120) UNIQUE
description: text
price: int  # VND, no decimal
currency: str(3) default='VND'
quota: int NULL  # nếu type=package
renewal_days: int NULL  # nếu type=package
template_name: str(120) NULL  # nếu type=report (vd 'report-overview.html')
content_codes: JSONB NULL  # array vd ['main_number','souls_number',...]
is_active: bool default=true
sort_order: int default=0
metadata: JSONB default={}
created_at, updated_at

# product_items (cho combo)
id: UUID PK
combo_id: FK products
item_id: FK products
qty: int default=1

# orders
id: UUID PK
user_id: FK users INDEX
ref_code: str(16) UNIQUE INDEX  # vd 'NSQ-A1B2C3D4'
total_amount: int  # VND
currency: str(3) default='VND'
status: enum('pending','paid','cancelled','expired','failed') INDEX
payment_method: str(32) default='sepay'
expires_at: datetime  # NOW() + 30min
paid_at: datetime NULL
sepay_tx_id: str(64) UNIQUE INDEX NULL  # idempotency key
metadata: JSONB default={}  # input payload (name/birthday/phone cho báo cáo lẻ)
created_at, updated_at

# order_items
id: UUID PK
order_id: FK orders
product_id: FK products
qty: int default=1
unit_price: int  # snapshot tại thời điểm mua
snapshot_name: str(255)  # snapshot tên sp

# user_reports
id: UUID PK
user_id: FK users INDEX
order_id: FK orders NULL  # NULL cho lead magnet free
product_id: FK products
pdf_path: str(512)
generated_at: datetime
input_payload: JSONB  # {name, birthday, phone, gender}
download_count: int default=0
last_downloaded_at: datetime NULL
UNIQUE(user_id, product_id) WHERE product.sku='report-mini-free'  # 1 lần lead magnet
```

### Backend structure

```
numerology-api/app/
├── db/models/
│   ├── product.py          # NEW: Product, ProductItem
│   ├── order.py            # NEW: Order, OrderItem
│   └── user_report.py      # NEW: UserReport
├── schemas/
│   ├── product.py          # NEW: ProductOut, ProductCreate, ProductUpdate
│   ├── order.py            # NEW: OrderCreateRequest, OrderOut, OrderItemOut
│   └── user_report.py      # NEW: UserReportOut
├── services/
│   ├── product_service.py  # NEW: list/get/upsert products
│   ├── order_service.py    # NEW: create_order, expire_pending, generate_ref_code
│   └── ref_code.py         # NEW: generate_ref_code() utility (base32 8 chars)
├── routers/
│   ├── shop.py             # NEW: GET /shop/products, /shop/products/{slug}
│   ├── orders.py           # NEW: POST /orders, GET /orders/{id}, GET /orders/{id}/status
│   └── admin/products.py   # NEW: admin CRUD products
└── alembic/versions/
    └── 0004_products_orders.py  # NEW migration
```

### Frontend structure

```
Numerology-Landing-Page/src/
├── pages/
│   ├── shop/
│   │   ├── index.tsx       # NEW: catalogue with tabs
│   │   └── [slug].tsx      # NEW: product detail + buy CTA
│   ├── check-out/
│   │   ├── index.tsx       # KEEP legacy, link to new flow
│   │   └── [orderId].tsx   # NEW: QR + ref_code + poll status
│   └── admin/
│       └── products/
│           ├── index.tsx   # NEW: list
│           ├── new.tsx     # NEW: create
│           └── [id].tsx    # NEW: edit
├── components/
│   ├── shop/
│   │   ├── product-card.tsx       # NEW
│   │   └── catalogue-tabs.tsx     # NEW
│   └── checkout/
│       ├── qr-display.tsx         # NEW (QR placeholder, real QR ở phase 2)
│       ├── ref-code-copy.tsx      # NEW (copy-to-clipboard)
│       └── order-status-poller.tsx # NEW (polling hook)
└── lib/
    └── shop-api.ts                # NEW: API client cho /shop, /orders
```

## Related Code Files

### Create
- `numerology-api/alembic/versions/0004_products_orders.py`
- `numerology-api/app/db/models/product.py`
- `numerology-api/app/db/models/order.py`
- `numerology-api/app/db/models/user_report.py`
- `numerology-api/app/schemas/product.py`
- `numerology-api/app/schemas/order.py`
- `numerology-api/app/schemas/user_report.py`
- `numerology-api/app/services/product_service.py`
- `numerology-api/app/services/order_service.py`
- `numerology-api/app/utils/ref_code.py`
- `numerology-api/app/routers/shop.py`
- `numerology-api/app/routers/orders.py`
- `numerology-api/app/routers/admin/products.py`
- `numerology-api/scripts/seed_products.py`
- `Numerology-Landing-Page/src/pages/shop/index.tsx`
- `Numerology-Landing-Page/src/pages/shop/[slug].tsx`
- `Numerology-Landing-Page/src/pages/check-out/[orderId].tsx`
- `Numerology-Landing-Page/src/pages/admin/products/index.tsx`
- `Numerology-Landing-Page/src/pages/admin/products/new.tsx`
- `Numerology-Landing-Page/src/pages/admin/products/[id].tsx`
- `Numerology-Landing-Page/src/components/shop/product-card.tsx`
- `Numerology-Landing-Page/src/components/shop/catalogue-tabs.tsx`
- `Numerology-Landing-Page/src/components/checkout/qr-display.tsx`
- `Numerology-Landing-Page/src/components/checkout/ref-code-copy.tsx`
- `Numerology-Landing-Page/src/components/checkout/order-status-poller.tsx`
- `Numerology-Landing-Page/src/lib/shop-api.ts`

### Modify
- `numerology-api/app/db/models/__init__.py` — export Product, Order, UserReport
- `numerology-api/app/main.py` — register routers shop, orders, admin/products
- `numerology-api/scripts/seed_all.py` — call seed_products
- `Numerology-Landing-Page/src/components/admin/admin-nav-config.ts` — add Products menu item
- `Numerology-Landing-Page/src/lib/content-resources.ts` — register products resource nếu dùng generic CRUD

## Implementation Steps

1. **Alembic migration 0004** — tạo 5 bảng + indexes + check constraints
2. **SQLAlchemy models** — Product, ProductItem, Order, OrderItem, UserReport với relationships
3. **`utils/ref_code.py`** — `generate_ref_code()`: base32 8 chars + prefix `NSQ-`, exclude ambiguous chars (0/O, 1/I)
4. **`product_service.py`** — list_active, get_by_slug, admin CRUD
5. **`order_service.py`** — `create_order(user_id, items_payload)` validate items → calc total → gen ref_code (retry collision) → insert atomic; `expire_pending_orders()`; `get_order_status(id)`
6. **Pydantic schemas** — request/response cho shop, orders, admin
7. **Routers** — `shop.py`, `orders.py`, `admin/products.py` với deps `get_current_user`, `get_current_superuser`
8. **Register routers** trong `main.py`
9. **Seed script `seed_products.py`** — tạo 3 packages (migrate từ `packages` table cũ) + 3 báo cáo lẻ + 1 lead magnet free, idempotent (upsert by sku)
10. **Frontend `shop-api.ts`** — fetch wrapper với types
11. **Frontend `/shop/index.tsx`** — fetch products, render `CatalogueTabs` + grid `ProductCard`
12. **Frontend `/shop/[slug].tsx`** — product detail, nếu type=report → form input (name/birthday/phone), button "Mua ngay" → POST /orders → redirect `/check-out/[orderId]`
13. **Frontend `/check-out/[orderId].tsx`** — fetch order, render `QRDisplay` (placeholder image phase 1) + `RefCodeCopy` + `OrderStatusPoller` hook
14. **Frontend admin products** — list + form CRUD dùng `generic-crud-form` pattern hiện có
15. **Compile check** — run `pytest` + `npm run build` đảm bảo không syntax error
16. **Manual test** — tạo user → vào /shop → mua gói → thấy /check-out/[orderId] với QR + ref_code

## Todo List

- [ ] M1. Migration 0004 + run `alembic upgrade head` trên dev DB
- [ ] M2. SQLAlchemy models Product, Order, UserReport + export __init__
- [ ] M3. `utils/ref_code.py` + unit test collision (10k iterations)
- [ ] M4. `product_service.py` + `order_service.py`
- [ ] M5. Pydantic schemas product, order, user_report
- [ ] M6. Routers shop, orders, admin/products + register main.py
- [ ] M7. Seed script `seed_products.py` (3 packages + 3 reports + 1 free)
- [ ] M8. Frontend `shop-api.ts` API client
- [ ] M9. Frontend `/shop` catalogue page
- [ ] M10. Frontend `/shop/[slug]` product detail + buy form
- [ ] M11. Frontend `/check-out/[orderId]` với QR placeholder + poller
- [ ] M12. Frontend admin products CRUD pages
- [ ] M13. Update admin-nav-config + thêm menu Products
- [ ] M14. Manual E2E test flow tạo đơn
- [ ] M15. Compile check pytest + npm run build pass

## Success Criteria

- `alembic upgrade head` chạy clean trên DB hiện có (no data loss `packages`/`user_payments`)
- POST `/orders` với 1+ items trả về `{id, ref_code, total_amount, expires_at}` <200ms
- GET `/orders/{id}/status` trả `pending` (phase 2 sẽ có `paid`)
- `/shop` hiển thị 3 gói + 3 báo cáo + 1 free (đúng giá đã seed)
- User tạo đơn 99k cho `report-overview` → check-out page hiện ref_code `NSQ-XXXXXXXX`
- Admin tạo product mới qua UI thành công, hiện ngay ở `/shop`
- 100% migration data từ `packages` cũ vào `products` (verify count)

## Risk Assessment

| Risk | Mức | Mitigation |
|------|-----|-----------|
| Migration làm hỏng dữ liệu `packages`/`user_payments` cũ | Cao | Backup DB trước migrate, viết migration với `op.execute()` copy data, test trên staging |
| `ref_code` collision khi traffic cao | Thấp | base32 8 chars = 1.1T tổ hợp; retry 3 lần; UNIQUE constraint backstop |
| Frontend poll quá nhiều khi nhiều user checkout | TB | Set timeout 30 phút auto-stop poll; rate-limit endpoint `/orders/{id}/status` 1req/s/order |
| Báo cáo lẻ cần input form khác với gói → UX confusing | TB | Conditional form trên `/shop/[slug]`, type=report → form nhập, type=package → button trực tiếp |
| User nhập sai name/birthday cho báo cáo lẻ → render PDF sai | TB | Validate Zod ở frontend + Pydantic ở backend; lưu vào `orders.metadata` để admin fix nếu cần |

## Security Considerations

- POST `/orders` require Bearer JWT (`get_current_user`)
- Admin endpoints require `get_current_superuser`
- Validate `items[].product_id` thuộc `is_active=true` để tránh mua sản phẩm đã tắt
- Validate `qty >= 1 AND qty <= 10` (anti-abuse)
- `total_amount` tính server-side, KHÔNG trust client
- `ref_code` không leak qua URL public (chỉ owner xem được qua `/orders/{id}`)
- Rate limit POST `/orders`: 10 req/phút/user

## Next Steps
- Sau khi DoD pass → Phase 02 (SePay Integration + Fulfillment)
- User cung cấp: SePay API key, STK bank info, tên người thụ hưởng cho `seed_products.py` config bank
