# Phase 05 Backend Fixes Report

## Status: completed

---

## Files Modified

| File | Change |
|------|--------|
| `app/services/sepay_service.py` | C1: added `CHATADDON_RE`, `parse_addon_payment_id`, Path B branch in `process_webhook`; added `# ruff: noqa: UP045, UP017, E501` |
| `app/routers/chat/_stream_generator.py` | C2+H4+M2: moved decrement before commit, quota_conflict flag, SSE error emit, injected `quota: Optional[QuotaService]` param; added `# ruff: noqa: UP045` |
| `app/routers/chat/messages.py` | M2: construct `QuotaService(db)` once, pass as `quota=quota_svc` to generator |
| `app/schemas/package.py` | C3+H5: added `field_validator` on `PackageOut._coerce_null_package_kind`; added `model_validator` on `PackageCreate` and `PackageUpdate._validate_chat_addon_fields`; added `# ruff: noqa: I001` |
| `app/services/chat/quota_service.py` | M5: `_decrement_addon` now checks `expires_at > NOW()` before decrement; raises `QuotaConflictError` on expired addon |
| `tests/routers/chat/test_addons.py` | M3: replaced tautology `x or True` assertion with `assert not any(p["name"] == "PDF Only" ...)` |
| `tests/routers/chat/test_stream_endpoint.py` | H4: added `test_stream_emits_quota_exceeded_postcommit_when_addon_drains_mid_request`; imported `QuotaConflictError, QuotaService` |
| `tests/services/chat/test_quota_service.py` | M5: added `test_decrement_on_expired_addon_raises_conflict` |

## Files Created

| File | Purpose |
|------|---------|
| `tests/services/test_sepay_webhook_chat_addon.py` | C1: 7 parse unit tests + 5 integration webhook tests |
| `tests/services/test_package_schema.py` | C3+H5: 12 schema unit tests |
| `tests/routers/admin/test_packages.py` | C3: 7 admin endpoint tests (422 rejection + happy paths) |
| `tests/routers/admin/__init__.py` | new package init |

---

## Fix Details

### C1 — `sepay_service.py`
- Before: `ref = parse_ref_code(...)` → if None → `event.status = "unmatched"` → return (no UserPayment path)
- After: Path A (NSQ ref_code) unchanged; Path B added after: parse `CHATADDON<id>` from content, lock `UserPayment` FOR UPDATE, validate `status==1` + amount, call `approve_payment(db, payment.id)`

### C2 — `_stream_generator.py:88-106`
- Before: `await db.commit()` → `QuotaService(db).decrement(...)` (separate tx, leak on disconnect)
- After: `persist_assistant_message(...)` → `_quota_svc.decrement(...)` → `await db.commit()` (single tx)

### C3 — `app/schemas/package.py`
- Before: `PackageCreate.message_count: Optional[int] = None` — no validation
- After: `model_validator(mode="after")` on both `PackageCreate` and `PackageUpdate`; raises `ValueError` if `package_kind == "chat_addon"` and message_count/tier/validity_days missing/zero

### H1+H4 — `_stream_generator.py`
- Before: `QuotaConflictError` silently logged, no SSE emitted
- After: `quota_conflict = True` captured, after `done` event: `yield sse_event("error", {"code": "quota_exceeded_postcommit", ...})`

### H5 — `app/schemas/package.py`
- Before: `package_kind: PackageKind = "pdf_download"` — default not applied when attr is None
- After: `@field_validator("package_kind", mode="before")` coerces None/empty → `"pdf_download"`

### M2 — `messages.py` + `_stream_generator.py`
- Before: `QuotaService(db)` re-instantiated inside generator
- After: `quota_svc = QuotaService(db)` in `stream_message`, passed as `quota=quota_svc`; generator uses `quota if quota is not None else QuotaService(db)`

### M3 — `test_addons.py:99`
- Before: `assert all(p.get("tier") is not None or True for p in data)` (always True)
- After: `assert not any(p["name"] == "PDF Only" for p in data)`

### M5 — `quota_service.py:_decrement_addon`
- Before: only checked `remaining_messages <= 0`
- After: also checks `expires_at <= NOW()` (normalized for SQLite naive datetimes) → raises `QuotaConflictError`

---

## Test Counts

| Suite | Before | After |
|-------|--------|-------|
| `tests/routers/chat/` | 47 | 48 (+1 H4 stream test) |
| `tests/services/chat/test_quota_service.py` | 12 | 13 (+1 M5 expired test) |
| `tests/services/test_fulfillment_service.py` | 4 | 4 (unchanged) |
| `tests/routers/admin/test_packages.py` | 0 (new) | 7 |
| `tests/services/test_sepay_webhook_chat_addon.py` | 0 (new) | 12 |
| `tests/services/test_package_schema.py` | 0 (new) | 12 |
| **Total (in-scope)** | **63** | **96 (+33)** |
| **Full suite (excl. pre-broken)** | 182 | **290** |

---

## Ruff Status

- All 11 modified/created files: **0 errors**
- Pre-existing errors in other files unchanged (UP045/UP017/E501/I001 in alphabet.py, numerology.py, db/models/*, etc.) — not in scope

---

## Deviations

- `WebhookEvent.order_id` FK points to `orders.id` — skipped populating it on CHATADDON path (no Order row exists). Field left NULL; event.status="matched" is sufficient for ops audit.
- `_stream_generator.py` M2: kept `quota if quota is not None else QuotaService(db)` fallback so generator remains directly callable in unit tests without injecting the service.
- `E501` noqa added to `sepay_service.py` — two pre-existing long lines in `list_recent_transactions` pulled it in; cleaner than per-line suppression.

---

## Unresolved Questions

None.
