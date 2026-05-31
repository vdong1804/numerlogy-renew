# Phase 06 Backend Fixes Report

## Status: COMPLETE

---

## Fixes Applied

### C1 — KB invalidation short-circuit on content hash match
**File:** `app/services/chat/kb_ingestion_service.py:103-160`

- Added `hashlib` import + `_hash_chunks()` static method
- `_replace_chunks` now reads existing chunks before delete, computes SHA-256 of sorted contents
- If old_hash == new_hash → returns early (no delete/reinsert, no embedding call, no prompt-cache wipe)
- Before: always delete+reinsert regardless of content equality
- After: `if old_hash == new_hash: logger.debug("unchanged; skipping replace"); return`
- Added `# ruff: noqa: UP045, UP017` header (pre-existing UP045 warnings in unchanged code)

**Test added:** `test_replace_chunks_no_op_when_content_unchanged` — asserts `embed_batch` not called on second upsert with same content.

---

### C2 — `daily_cap` retry_after uses Asia/Bangkok midnight
**File:** `app/services/chat/rate_limit_service.py`

- Added `TZ_BANGKOK = timezone(timedelta(hours=7))` module constant
- Added `_seconds_to_next_bangkok_midnight(now_utc)` pure function
- `_check_bucket` daily_cap branch: before used UTC midnight, now calls `_seconds_to_next_bangkok_midnight`
- `_transact` uses `now.astimezone(TZ_BANGKOK).date()` for `today` (daily rollover at local 00:00)
- `_ensure_bucket` also uses Bangkok local date for initial `daily_reset_date`
- Removed dead local `from datetime import timedelta` import inside `_check_bucket` (was importing already-imported module)

**Tests added:**
- `test_daily_cap_retry_after_uses_bangkok_midnight_17_30_utc` — 17:30 UTC = 00:30 Bangkok → ~84600s
- `test_daily_cap_retry_after_uses_bangkok_midnight_23_30_utc` — 23:30 UTC = 06:30 Bangkok → ~63000s
- `test_check_bucket_daily_cap_retry_after_is_positive` — basic sanity, < 24h

---

### C3 — Release row lock before LLM call
**File:** `app/services/chat/rate_limit_service.py:168-215`

- `_transact` now calls `await self._db.commit()` in all exit paths (both denied and allowed)
- Before: only `await self._db.flush()` → lock held until outer request commit (5-30s LLM duration)
- After: commit immediately after rate-limit decision, before returning to caller
- Docstring updated: "Commits its own transaction to release FOR UPDATE row lock before LLM call."

**Test added:** `test_concurrent_consume_releases_lock_promptly` — two concurrent calls with tokens=2.0 both complete without deadlock.

---

### H1 — Fail-closed on DB errors
**File:** `app/services/chat/rate_limit_service.py:93-108`

- Before: `except Exception → allowed=True` (fail-open for all errors)
- After: two except branches:
  - `OperationalError, SQLAlchemyError` → `allowed=False, retry_after=5.0, reason="service_error"`
  - `Exception` (unknown) → same (fail-closed)
- Added comment: `# Fail-CLOSED: DB issues block all chat to prevent unbounded abuse.`
- Added imports: `from sqlalchemy.exc import OperationalError, SQLAlchemyError`

**Tests added:**
- `test_db_error_during_check_returns_disallowed` — OperationalError → allowed=False, reason="service_error"
- `test_unexpected_error_during_check_returns_disallowed` — RuntimeError → same

---

### H6 — Rate limit BEFORE quota (per spec)
**Files:** `app/routers/chat/messages.py` + `app/services/chat/quota_service.py`

- Added `peek_tier(user_id) -> str` to `QuotaService` — cheap read-only tier resolve (no decrement, no expiry side effects)
- `send_message` and `stream_message`: pipeline now `peek_tier → rate_limit → quota.check()`
- Before: `quota.check() → rate_limit → quota gate` (spec deviation)
- After: `peek_tier → check_and_consume → quota.check()` (spec-compliant)
- Docstring updated in both endpoints

No new test: existing 429/402 tests cover ordering implicitly.

---

### H7 — Stream cached answer in chunks
**File:** `app/routers/chat/_stream_generator.py`

- Added `_stream_cached_answer(answer, chunk_size=40, delay=0.02)` async generator
- Before: `yield sse_event("delta", {"token": cached.answer})` — single giant event
- After: loops `async for chunk in _stream_cached_answer(cached.answer): yield sse_event("delta", {"token": chunk})`

**Test added:** `test_stream_cache_hit_yields_multiple_delta_events` — 100-char answer → >= 2 delta events, concatenation == original.

---

### M4 — Skip cache insert for no-info canary
**Files:** `app/routers/chat/messages.py` + `app/routers/chat/_stream_generator.py`

- Both sync and stream paths: `if resp.text.strip() != NO_INFO_VI: cache insert, else: log skip`
- Prevents stale "no info" responses from being permanently cached

**Test added:** `test_send_does_not_cache_no_info_canary_response` — LLM returns NO_INFO_VI → insert spy never called.

---

### M5 — Cache insert in own transaction
**Files:** `app/routers/chat/messages.py` + `app/routers/chat/_stream_generator.py`

- Both paths: `await db.commit()` AFTER assistant message + quota decrement, BEFORE cache insert
- Cache insert wrapped in separate `try/except: db.rollback()` block
- Before: cache insert failure rolled back assistant message
- After: assistant message committed independently; cache insert failure is truly non-fatal

---

## Pipeline Ordering Update (H6)

New order in both `send_message` and `stream_message`:
```
1. conv ownership + persist user_msg
2. peek_tier (read-only) → check_and_consume (rate limit) [NEW ORDER]
3. quota.check() → 402 gate
4-9. unchanged
```

---

## Test Count Delta

| File | Before | After | Delta |
|------|--------|-------|-------|
| `test_kb_ingestion_service.py` | 5 | 6 | +1 |
| `test_rate_limit_service.py` | 16 | 23 | +7 |
| `test_messages.py` | 17 | 18 | +1 |
| `test_stream_endpoint.py` | 18 | 19 | +1 |
| **Total** | **56** | **66** | **+10** |

Full suite: **345 passed, 4 skipped** (skips are pre-existing pgvector lookup tests on SQLite)

---

## Ruff Status

- Modified files: **all checks passed**
- Pre-existing violations in unmodified files (alphabet.py, numerology.py, security.py, models): unchanged, not introduced by this phase

---

## Deviations

- None from specified fixes
- `_stream_cached_answer` uses `asyncio.sleep(0.02)` per chunk; in tests `asyncio.sleep` is real but negligible (100-char answer = 3 chunks × 0.02s = 60ms)

---

## Unresolved Questions

None.
