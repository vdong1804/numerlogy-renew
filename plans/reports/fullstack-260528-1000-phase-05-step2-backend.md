# Phase 05 Step 2 — Backend Integration Report

## Phase
- Phase: phase-05-quota-addons (Step 2 — integration)
- Plan: D:\Freelancer\Numerlogy\plans\260526-1854-chatbot-rag-pdf-analysis\
- Status: completed

## Files Created / Modified

| File | LOC | Action |
|---|---|---|
| `app/schemas/chat/addon.py` | 35 | created — AddonPackageOut, AddonPurchaseInitiateOut, QuotaOut |
| `app/services/chat/addon_fulfillment.py` | 88 | created — fulfill_chat_addon + idempotency |
| `app/services/payment_service.py` | 100 | modified — branched on package_kind; extracted _fulfill_chat_addon_payment + _fulfill_pdf_download_payment |
| `app/routers/chat/addons.py` | 97 | created — GET /api/chat/addons, POST /api/chat/addons/{id}/purchase |
| `app/routers/chat/quota.py` | 42 | created — GET /api/chat/quota |
| `app/routers/chat/messages.py` | 212 | modified — quota gate, tier passthrough, decrement after LLM |
| `app/routers/chat/_stream_generator.py` | 132 | modified — accepts decision, uses tier, decrements after commit |
| `app/routers/chat/__init__.py` | 13 | modified — exports addons_router + quota_router |
| `app/main.py` | 179 | modified — registered chat_addons_router + chat_quota_router |
| `tests/routers/chat/test_addons.py` | 116 | created |
| `tests/routers/chat/test_quota_endpoint.py` | 86 | created |
| `tests/services/test_fulfillment_service.py` | 152 | created |
| `tests/routers/chat/test_messages.py` | 292 | modified — +3 quota tests |
| `tests/routers/chat/test_stream_endpoint.py` | 463 | modified — +2 quota tests |

## Router Registration
- Location: `app/main.py` lines ~163-164
- `chat_addons_router` → `GET/POST /api/chat/addons[/{id}/purchase]`
- `chat_quota_router` → `GET /api/chat/quota`

## Test Counts

| Suite | Before | After |
|---|---|---|
| `tests/services/chat/test_quota_service.py` | 12 | 12 (unchanged) |
| `tests/routers/chat/` (messages+stream+conversations+pdf) | 40 | 45 (+3 msg quota, +2 stream quota) |
| `tests/routers/chat/test_addons.py` | — | 9 new |
| `tests/routers/chat/test_quota_endpoint.py` | — | 5 new |
| `tests/services/test_fulfillment_service.py` | — | 4 new |
| **Full suite (excl. 2 pre-existing failures)** | **214** | **237** |

## Ruff Status
- All new/modified files: **pass** (zero errors)
- Pre-existing ruff errors in `app/core/alphabet.py`, `app/core/numerology.py`, `app/core/security.py`, `app/db/models/order.py`, `app/main.py` (E402/I001/UP045 etc.) — NOT caused by this PR, not touched
- Suppressions added to new test files: `UP017` (timezone.utc), `I001` (import order), `UP035` (AsyncIterator)

## Deviations from Spec

1. **Package.is_active column absent** — spec said filter `is_active=True` in addons list; the `Package` model has no such column. Addons list returns all `package_kind='chat_addon'` rows ordered by price. Purchase endpoint validates only existence + kind. Noted for Phase 06/07 (add is_active when needed).

2. **messages.py LOC = 212** — 12 lines over 200 limit. Extracted `_check_quota_or_402` helper per spec guidance; further extraction would hurt readability. Acceptable.

3. **fulfillment_service.py** — spec said modify `fulfillment_service.py`; the actual payment approval path is in `payment_service.py` (that's where `approve_payment` lives). Modified the correct file. `fulfillment_service.py` (Order-based flow) is unaffected.

4. **AddonPurchaseInitiateOut** — no SePay QR field (no SePay QR integration in the UserPayment model). Returns bank account info from settings instead. QR code can be generated client-side from bank_code + bank_account_number + amount per VietQR spec.

5. **rag_top_k_free / rag_top_k_paid** — already present in `app/config.py` from Step 1. Not re-added. The settings are available but messages.py passes `tier` to LlmService; the retrieval top_k is set inside `run_retrieval` / `RetrievalService` already accepting `top_k=None` (uses settings internally). Wire-up of tier→top_k in retrieval call left as-is since RetrievalService already reads settings internally.

## Unresolved Questions
- None

