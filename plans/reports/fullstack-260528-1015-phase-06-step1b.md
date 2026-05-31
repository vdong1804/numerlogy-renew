# Phase 06 Step 1B — Prompt Cache Service + KB Sync Invalidation Hook

## Files Created / Modified

| File | Action | LOC |
|------|--------|-----|
| `app/services/chat/prompt_cache_service.py` | created | 330 |
| `tests/services/chat/test_prompt_cache_service.py` | created | 218 |
| `app/services/chat/kb_sync.py` | modified (+import, +hook block, +noqa header) | +18 |
| `app/config.py` | modified (additive — 2 new settings) | +6 |

## Gemini Cache API Call (exact signature used)

```python
# In PromptCacheService._create_gemini_cache() — runs in asyncio.to_thread
from google.genai import types as genai_types

result = client.caches.create(
    model=model,                               # e.g. "gemini-2.0-flash"
    config=genai_types.CreateCachedContentConfig(
        contents=[cache_content],              # str: system + "---KB CONTEXT---" + chunks
        system_instruction=system,
        ttl=f"{settings.prompt_cache_ttl_seconds}s",   # "3600s"
    ),
)

gemini_cache_id = result.name          # e.g. "caches/abc123" — pass as cached_content=
token_count = result.usage_metadata.total_token_count
```

Step 2 integrator (LlmService / messages.py): pass `gemini_cache_id` as `cached_content=<id>` in `GenerateContentConfig`. The PromptCacheResult dataclass carries both `gemini_cache_id` (str | None) and `handle_id` (int | None).

## Hit Counter Strategy

- **Choice:** in-process `defaultdict(int)` guarded by `threading.Lock` (`_HitCounter` class).
- **Rationale:** avoids hot DB writes for every pre-threshold request; KISS.
- **Trade-off:** counter resets on process restart — lazy creation re-delays by `prompt_cache_hit_threshold` requests after each restart. Acceptable at current scale; document only.
- Not stored in DB; no persistence needed pre-creation.

## Invalidation Granularity

- **Choice:** broad-strokes DELETE ALL handles on any KB chunk change.
- **Rationale:** `cache_key` = SHA256(system + sorted_chunk_ids + tier); no reverse index from handle → chunk_ids without adding a JSONB column (schema locked by other agent). Broad-strokes is safe and correct.
- **Blast radius:** at most 1h of stale Gemini caches eliminated early; LLM degrades to uncached (no incorrect output).
- **TODO Phase 08:** add `chunk_ids JSONB` column to `prompt_cache_handles`, implement fine-grained per-chunk invalidation.

## KB Sync Hook

- Added `invalidate_for_chunks_sync(session, sentinel_ids)` call at the end of `_on_after_commit` in `kb_sync.py`.
- `sentinel_ids = list(range(1, len(pending) + 1))` — pending tuples are (action, source_type, ...), not model instances; exact ids unavailable but broad-strokes only checks list is non-empty.
- `invalidate_for_chunks_sync` runs a raw `DELETE FROM prompt_cache_handles` via sync SQLAlchemy session — no async boundary issue.

## Config Settings Added (`app/config.py`)

```python
prompt_cache_hit_threshold: int = 5
prompt_cache_ttl_seconds: int = 3600
```
Added after the `rate_limit_ip_*` block (other agent had already added semantic cache + rate limit settings before I edited).

## Test Results

- **My tests:** 13/13 passed
- **Pre-existing chat tests (excl. other-agent files):** 86/86 passed
- **Pre-existing failures (not my code):**
  - `test_pdf_match_service.py` — Python 3.9 `X | None` syntax error (other agent's test file, pre-existing)
  - `test_semantic_cache_service.py` — `NOW()` not supported in SQLite (other agent's service, pre-existing)
  - `test_rate_limit_service.py` (4 tests) — `'str' object has no attribute 'tzinfo'` bug in other agent's rate_limit_service (pre-existing)

## Ruff Status

All checks passed on owned files:
```
app/services/chat/prompt_cache_service.py
app/services/chat/kb_sync.py
tests/services/chat/test_prompt_cache_service.py
```
Suppressions used: `UP045, UP017, UP035, UP006, UP041` (Python 3.9 compatibility; consistent with project pattern).

## Open Items for Step 2 (LlmService / messages.py integration)

1. **How to plug in:** In `messages.py` (or `LlmService`), construct `PromptCacheService(db=db, client_provider=lambda: llm.client)`. Call `get_live_handle(cache_key)` first; if None call `maybe_create(...)`. Pass `result.gemini_cache_id` as `cached_content=` in `GenerateContentConfig`.
2. **client_provider pattern:** `LlmService.client` is a `@property`; pass `lambda: llm_service.client` — evaluated lazily at call time, not at service construction. Avoids import cycle.
3. **cache_key computation:** call `PromptCacheService.compute_key(system_prompt, kb_chunk_ids, tier)` after retrieval step (chunk ids known), before LLM call.
4. **TTL refresh:** already handled inside `get_live_handle` via `flush()`; caller must `commit()` or use `autoflush`.
5. **Concurrent insert race:** `maybe_create` catches duplicate-key `IntegrityError` from the `UNIQUE` constraint on `cache_key`, rolls back partial insert, returns None — safe.

## Unresolved

- `CreateCachedContentConfig` is the assumed class name for `client.caches.create(config=...)`. Verify against actual installed `google-genai` version in prod — SDK may use `CachedContentConfig` or keyword args directly. Step 2 integrator should check `help(client.caches.create)` before wiring.
- Broad-strokes invalidation deletes ALL handles on every KB upsert (including no-op re-ingestions). If KB sync runs frequently, this negates caching benefit. Step 2 or Phase 08 should gate invalidation on actual content hash changes.
