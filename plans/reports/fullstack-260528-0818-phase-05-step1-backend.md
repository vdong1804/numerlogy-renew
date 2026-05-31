# Phase 05 Step 1 — Backend Foundation Report

## Phase
- Phase: phase-05-quota-addons (Step 1 only)
- Plan: D:\Freelancer\Numerlogy\plans\260526-1854-chatbot-rag-pdf-analysis\
- Status: completed

## Files Modified / Created

| File | LOC | Action |
|---|---|---|
| `alembic/versions/0012_chat_addons.py` | 105 | created |
| `app/db/models/chat/chat_addon_purchase.py` | 61 | created |
| `app/db/models/chat/__init__.py` | 20 | modified (added ChatAddonPurchase import) |
| `app/db/models/package.py` | 99 | modified (4 new fields + noqa header) |
| `app/services/chat/quota_service.py` | 201 | created |
| `app/config.py` | 113 | modified (chat_free_daily_limit + noqa suppressions) |
| `tests/services/chat/test_quota_service.py` | 357 | created |

## Migration Revision
- ID: `0012`, down_revision: `0011`
- Adds: `packages.package_kind`, `packages.message_count`, `packages.tier`, `packages.validity_days`
- Creates: `chat_addon_purchases` table + partial index `chat_addon_user_active_idx WHERE is_active = true`
- `chat_quota_usage` — ALREADY EXISTS (created in 0010 with `free_used`/`paid_used` columns) — skipped

## chat_quota_usage Status
- Existed in migration 0010 with composite PK `(user_id, date)`, columns: `free_used INT`, `paid_used INT`
- Model at `app/db/models/chat/quota_usage.py` — already registered
- QuotaService uses `free_used` column (not `count`); upsert SQL targets correct column name

## Test Results
- `tests/services/chat/test_quota_service.py`: **12/12 passed** (5.86s)
- Full suite (excluding 2 pre-existing failures): **214/214 passed** (45s)
- Pre-existing failures (not caused by this work):
  - `tests/services/chat/test_pdf_match_service.py` — `str | None` syntax error at import (Python 3.9 incompatibility, existed before this PR)
  - `tests/integration/test_admin_content.py::test_admin_content_list_superuser` — KeyError `data` (pre-existing)

## Ruff Status
- All checks passed on all 7 files
- Required `# ruff: noqa` suppressions:
  - `UP045` in `package.py` + `chat_addon_purchase.py` — `Optional[X]` in `Mapped[...]` required for SQLAlchemy on Python 3.9
  - `UP017` in `quota_service.py`, `test_quota_service.py`, `config.py` — `datetime.UTC` is Python 3.11+, runtime is 3.9

## Python 3.9 Compatibility Notes
- Ruff targets py312 per `pyproject.toml` but runtime is Python 3.9
- `str | None` union syntax inside `Mapped[...]` fails even with `from __future__ import annotations` because SQLAlchemy 2.0 calls `get_type_hints()` which evaluates forward refs at runtime
- `Pydantic 2` also evaluates annotations at class-definition time — `Optional[str]` required in `Settings`
- `datetime.UTC` introduced in 3.11 — must use `timezone.utc`
- All three issues resolved with `# ruff: noqa` to avoid re-triggering on next `--fix`

## Sanity Import
```
python3 -c "from app.services.chat.quota_service import QuotaService, QuotaDecision, QuotaBalance, QuotaConflictError; print('ok')"
# → ok
```

## Open Follow-ups for Step 2

### messages.py router
- Import `QuotaService`; call `await quota.check(user.id)` before retrieval/LLM
- On `can_send=False` raise `HTTPException(402, detail={"code": "quota_exceeded", "upsell": True})`
- Call `await quota.decrement(user.id, decision)` after successful streaming response
- Pass `decision.tier` to `LlmService.generate_stream(tier=...)` and `RetrievalService.retrieve(top_k=...)`

### fulfillment_service.py
- Branch on `pkg.package_kind == "chat_addon"` → call `addon_fulfillment.create_purchase()`
- `addon_fulfillment.py` inserts `ChatAddonPurchase(remaining_messages=pkg.message_count, expires_at=NOW()+validity_days, ...)`

### llm_service.py / retrieval_service.py
- Already accept `tier` param (confirmed in stream test fixtures) — no signature change needed
- Verify `rag_top_k_free` / `rag_top_k_paid` are being passed from messages router

## Unresolved Questions
- None for Step 1; all deliverables complete and tested
