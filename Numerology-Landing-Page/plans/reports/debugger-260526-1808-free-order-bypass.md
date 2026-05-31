# Bug: Free Product Still Requires Payment

**Reported:** `/check-out/2/` — free product, yet UI shows QR + asks to pay 0₫.

## Root Cause

`numerology-api/app/services/order_service.py::create_order` unconditionally creates orders with `status="pending"`, regardless of `total_amount`. For free products `total = 0`, but the order still enters the pending-payment flow.

Frontend `pages/shop/[slug].tsx::handleBuy` then always routes the user to `/check-out/[orderId]`, which renders `QrDisplay` and starts the SePay status poller — a useless QR for 0₫ and an order that never resolves to `paid`.

**Chain:**
1. `create_order` → `total=0`, `status="pending"` (no special branch) ← **bug origin**
2. `shop/[slug] handleBuy` → unconditional `router.push('/check-out/${id}')`
3. `check-out/[orderId]` → renders QR, polls indefinitely

## Fix

Three layers (defense-in-depth):

### 1. Backend (authoritative) — `order_service.create_order`
After eager-loading items, if `total == 0`:
- Set `status="paid"`, `paid_at=now(UTC)`
- Call `fulfillment_service.fulfill_order` inline (best-effort: try/except logs)
- Return the now-paid order

Server is the source of truth; fulfillment must run server-side anyway (PDF render, quota grant).

### 2. Frontend `shop/[slug].tsx::handleBuy`
After `createOrder`, if `order.status === 'paid'` OR `order.total_amount === 0`, redirect directly to `/my-account/reports` (report-type product) or `/my-account` (package/combo). Skip the QR page entirely.

### 3. Frontend `check-out/[orderId].tsx` — safety net
On direct-link visits, an effect inspects the loaded order. If `total_amount === 0` or `status === 'paid'`, `router.replace()` to the appropriate destination. Prevents stale URLs / bookmarks from landing on the QR page.

## Files Changed
| File | Change |
|---|---|
| `numerology-api/app/services/order_service.py` | +20 LOC — free-order auto-pay + fulfillment branch |
| `Numerology-Landing-Page/src/pages/shop/[slug].tsx` | +5 LOC — skip QR on paid/free |
| `Numerology-Landing-Page/src/pages/check-out/[orderId].tsx` | +11 LOC — safety-net redirect effect |

## Verification
- ✓ `tsc --noEmit` — zero errors in touched files
- ✓ `python -m py_compile` — order_service.py compiles
- ⚠ pytest blocked by **pre-existing** UnicodeDecodeError in `tests/conftest.py` env-file loader (cp1252 vs UTF-8). Unrelated to this fix.

## Unresolved Questions
- Existing `pending` orders with `total_amount=0` in the DB (e.g., the user's order id=2): not auto-fixed by this code change. Need a one-off backfill or manual `UPDATE orders SET status='paid', paid_at=now() WHERE total_amount=0 AND status='pending'` + manual `fulfill_order` call. Confirm with user whether to write a migration / script.
- Fulfillment failure on free orders: currently logs and swallows. Consider: should the user see an error instead of a silent broken flow? Current behavior keeps order alive so support can re-run, but UX-wise the user is redirected to /my-account where no report appears.
- Pre-existing `tests/conftest.py` UnicodeDecodeError — should be fixed separately (encoding spec on the env loader).
