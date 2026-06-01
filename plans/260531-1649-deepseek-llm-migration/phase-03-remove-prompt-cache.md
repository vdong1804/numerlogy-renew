# Phase 03 — Remove Prompt-Cache Layer

## Context Links
- Parent: [plan.md](./plan.md)
- Depends on: P1, P2.
- Code touched (verified via grep):
  - `numerology-api/app/services/chat/prompt_cache_service.py` (DELETE)
  - `numerology-api/app/db/models/chat/prompt_cache_handle.py` (DELETE)
  - `numerology-api/app/db/models/chat/__init__.py` (drop import + __all__ entry)
  - `numerology-api/app/routers/chat/messages.py` (strip step 6)
  - `numerology-api/app/routers/chat/_stream_generator.py` (strip step 6)
  - `numerology-api/app/services/chat/kb_sync.py` (drop import + invalidate call)
  - `numerology-api/app/jobs/cleanup_semantic_cache.py` (strip prompt_cache half)
  - `numerology-api/app/jobs/scheduler.py` (no change — job stays; cleans semantic_cache only)
  - `numerology-api/alembic/versions/` (NEW migration: drop table)
- Initial schema reference: `497b2cb25f8d_initial_schema.py:318` creates `prompt_cache_handles`; line 786 drops in downgrade (kept for completeness).

## Overview
- **Priority:** P0.
- **Status:** pending.
- Rip out everything related to Gemini explicit prompt-cache. DeepSeek does context caching automatically (free, transparent).

## Key Insights
- `prompt_cache_handles` has no FKs to other tables (verified — initial-schema column list is self-contained). Safe to `DROP TABLE` without cascade.
- `invalidate_for_chunks_sync` is the only prompt-cache symbol called from `kb_sync.py` (after_commit hook). Removing the call leaves the kb-sync queue logic intact.
- `cleanup_semantic_cache.py` runs nightly — strip prompt_cache half but keep file + scheduler entry; semantic_cache cleanup still required.
- `_build_prompt_cache_svc` helper in `messages.py:124` becomes dead — delete.
- `llm.client` reference in `_stream_generator.py:141` and `messages.py:227` was passed to PromptCacheService.client_provider — both call sites die with prompt-cache removal, so `LlmService.client` becomes unused externally (but still needed internally in P2 rewrite).

## Requirements
- All callers of `PromptCacheService` / `prompt_cache_handles` / `invalidate_for_chunks_sync` removed.
- New alembic migration drops `prompt_cache_handles` table.
- `cleanup_semantic_cache` job still runs but only cleans `semantic_cache` table.
- No behavioral regression in semantic-cache or kb-sync paths.

## Architecture

### Before
```
chat_turn → SemanticCache.lookup → miss
         → PromptCacheService.get_live_handle / maybe_create → gemini_cache_id
         → LlmService.generate(cached_content=gemini_cache_id)
         → SemanticCache.insert
```

### After
```
chat_turn → SemanticCache.lookup → miss
         → LlmService.generate(prompt) // DeepSeek auto-caches server-side
         → SemanticCache.insert
```

## Related Code Files

**Modify**
- `app/db/models/chat/__init__.py` — remove `PromptCacheHandle` import + from `__all__`.
- `app/routers/chat/messages.py`:
  - Remove `from app.services.chat.prompt_cache_service import PromptCacheService` (line 42).
  - Remove `_build_prompt_cache_svc` (lines 124-125).
  - Remove "Step 6: prompt cache" block (lines 225-244) — `pc_svc`, `cache_key`, `pc_result`, `maybe`, `gemini_cache_id`.
  - Remove `cached_content=gemini_cache_id` arg from `llm.generate(...)` (line 252).
  - Update module docstring (drop step 6).
- `app/routers/chat/_stream_generator.py`:
  - Remove PromptCacheService import (line 37).
  - Remove "Step 6: prompt cache lookup / maybe_create" block (lines 140-158).
  - Remove `cached_content=gemini_cache_id` from `llm.generate_stream(...)` call (line 167).
  - Update module docstring.
- `app/services/chat/kb_sync.py`:
  - Remove `from app.services.chat.prompt_cache_service import invalidate_for_chunks_sync` (line 26).
  - Remove `sentinel_ids = ...` + `invalidate_for_chunks_sync(...)` call in `_on_after_commit` (lines 94-102).
  - Trim docstring of `_on_after_commit` accordingly.
- `app/jobs/cleanup_semantic_cache.py`:
  - Remove PromptCacheService import + instantiation + `cleanup_expired` call.
  - Update return dict to only `{"semantic_cache": N}`.
  - Update log line.
- `app/jobs/scheduler.py` — no change (job still runs; same id).

**Delete**
- `app/services/chat/prompt_cache_service.py`
- `app/db/models/chat/prompt_cache_handle.py`

**Create**
- `alembic/versions/<rev>_drop_prompt_cache_handles.py` — new migration:
  - `op.drop_table('prompt_cache_handles')` in `upgrade()`.
  - `op.create_table(...)` mirroring initial-schema columns in `downgrade()` (for rollback safety).
  - `down_revision` = current head (run `alembic current` to confirm; initial migration `497b2cb25f8d` may still be head if no later migrations exist).

## Implementation Steps
1. **Code-side strip** (in order to avoid import errors):
   1. Delete prompt-cache call sites in `_stream_generator.py` and `messages.py`.
   2. Delete `invalidate_for_chunks_sync` import + call in `kb_sync.py`.
   3. Strip `cleanup_semantic_cache.py` prompt-cache half.
   4. Remove `PromptCacheHandle` from `db/models/chat/__init__.py`.
   5. Delete `app/services/chat/prompt_cache_service.py`.
   6. Delete `app/db/models/chat/prompt_cache_handle.py`.
2. **Migration**:
   1. `alembic revision -m "drop prompt_cache_handles"` (or hand-author with timestamp).
   2. Fill `upgrade()` with `op.drop_table('prompt_cache_handles')`.
   3. Fill `downgrade()` with table re-create mirroring schema at `497b2cb25f8d:318-328`.
3. **Verification greps** (must return empty):
   - `grep -rn "PromptCache\|prompt_cache_handle\|invalidate_for_chunks\|cached_content" numerology-api/app`
   - `grep -rn "from app.services.chat.prompt_cache_service" numerology-api`
4. **Compile**: `python -m compileall app/routers/chat app/services/chat app/jobs app/db/models/chat`.
5. **Migration smoke**: `alembic upgrade head` against a scratch DB.

## Todo List
- [ ] Strip prompt-cache block from `_stream_generator.py` (incl. `cached_content` kwarg)
- [ ] Strip prompt-cache block from `messages.py` (incl. helper + kwarg)
- [ ] Strip `invalidate_for_chunks_sync` from `kb_sync.py`
- [ ] Strip prompt-cache half from `cleanup_semantic_cache.py`
- [ ] Remove `PromptCacheHandle` from `db/models/chat/__init__.py` (`__all__` + import)
- [ ] Delete `prompt_cache_service.py`
- [ ] Delete `prompt_cache_handle.py`
- [ ] New alembic migration: drop `prompt_cache_handles`
- [ ] `alembic upgrade head` on scratch DB succeeds
- [ ] All verification greps return empty
- [ ] `python -m compileall` succeeds

## Success Criteria
- `pytest tests/ -k "not prompt_cache"` collects without import errors (P4 then handles test cleanup).
- `alembic upgrade head` + `alembic downgrade -1` round-trips without error.
- Chat send/stream still serves a response via DeepSeek (P2 + this phase together).
- No references to Gemini prompt cache anywhere in `app/`.

## Risk Assessment
| Risk | L | I | Mitigation |
|------|---|---|-----------|
| Production DB has live `prompt_cache_handles` rows | H | L | DROP TABLE handles this; alembic migration safe |
| Concurrent code deploy + migration ordering | M | M | Runbook: deploy code first (no callers), then run migration |
| Test imports break (test_prompt_cache_service.py) | H | L | Deleted in P4 |
| Forgotten reference causes import-time crash | M | H | Verification greps in step 3; CI catches |
| Downgrade lost the `gemini_cache_id` data | H | L | Acceptable — feature deleted, data not recoverable; documented |

## Security Considerations
- No secrets in table — only Gemini cache ids (which are short-lived references). Safe to drop.
- Migration runs as DB owner; no privilege change needed.

## Next Steps
- P4: delete `tests/services/chat/test_prompt_cache_service.py`, update `tests/jobs/test_cleanup_semantic_cache.py`, strip prompt-cache mocks from `tests/routers/chat/test_messages.py` + `test_stream_endpoint.py`.
- P5: doc sync.
