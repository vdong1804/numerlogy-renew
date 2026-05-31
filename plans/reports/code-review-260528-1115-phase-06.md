# Phase 06 Code Review

## Summary (pass with fixes)

Phase 06 is largely solid: semantic cache, rate limit, prompt cache, cleanup job, and the FE 429 flow are wired through both sync and stream paths. The pipeline order is consistent, fixtures correctly stub the cache for legacy tests, and cache-hit tests verify the critical behaviours (LLM skipped, quota decremented, `from_cache=True`).

Blocking issues are few but real: prompt-cache invalidation fires on every KB re-sync (including no-op upserts) because `KbIngestionService._replace_chunks` always deletes+reinserts chunks. This effectively defeats prompt caching whenever KB sync is exercised. Two additional items (rate-limit fail-open policy decision, daily_cap retry-after math wraparound) need explicit decisions before launch.

Recommendation: **pass with fixes** — ship after addressing C1, C2, and H1.

---

## Critical (3)

### C1. Prompt-cache invalidation triggers on every KB re-sync, even no-op
`app/services/chat/kb_sync.py:75-102` + `app/services/chat/kb_ingestion_service.py:103-131`

`_on_after_commit` calls `invalidate_for_chunks_sync(session, sentinel_ids)` whenever `pending` is non-empty. `pending` is populated by mapper-level `after_insert/after_update/after_delete` on numerology tables. Every routine `update` on a numerology row stashes an item → triggers `_on_after_commit` → nukes all `prompt_cache_handles`.

Worse: `KbIngestionService._replace_chunks` (`kb_ingestion_service.py:119`) unconditionally executes `DELETE FROM kb_chunks WHERE document_id = …` and re-inserts. So even a "no-content-changed" upsert fires the cache invalidation. With KB writes during normal admin editing, the 5-hit threshold is rarely reached before the next invalidation wipes the prompt cache — the 75% cost reduction never materializes.

Fix options:
- **Quick:** Hash content in `_replace_chunks`; skip rebuild if hash unchanged. Stash only when actually changed.
- **Proper:** Compare content hash in `_get_or_create_document` and short-circuit `_replace_chunks` when content equals stored hash. Bonus: avoids redundant embedding calls.
- **Stopgap:** Only call `invalidate_for_chunks_sync` for `delete` actions, OR gate it on a `KB_INVALIDATE_PROMPT_CACHE=true` env flag so staging can verify behaviour before prod.

Severity: critical. Defeats the entire cost-optimization goal of Phase 06.

---

### C2. `daily_cap` retry-after calculation has a wraparound bug at end-of-day
`app/services/chat/rate_limit_service.py:300-307`

```python
now = datetime.now(timezone.utc)
tomorrow = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
tomorrow = tomorrow + timedelta(days=1)
retry = math.ceil((tomorrow - now).total_seconds())
```

At 23:59:30 UTC the retry is ~30s — correct. But on 31 Jan at 23:59 UTC, `datetime(2026, 1, 32, ...)` would fail; instead, `now.day` is fine because `timedelta(days=1)` handles the rollover. So no exception. **However**: scheduler is `Asia/Bangkok` (UTC+7), and `daily_reset_date` semantics in `_apply_refill` use the `today` value passed in, which is `datetime.now(timezone.utc).date()`. Mismatch: `tomorrow` reset is computed in UTC, but if buckets are intended to reset on Bangkok midnight, the rollover is 7h off. Either:
- Document explicitly that daily caps reset at UTC midnight (current behaviour), OR
- Align both `daily_reset_date` and the `tomorrow` math to Bangkok TZ.

Phase 06 spec says "daily 100" / "daily 1000" without specifying TZ. Pick one and document. Users in VN seeing 100/day reset at 7 AM local time is surprising.

Severity: critical-for-UX; pick a TZ now to avoid breaking-change later.

---

### C3. `RateLimitService.check_and_consume` `_ensure_bucket` runs OUTSIDE the SELECT FOR UPDATE block
`app/services/chat/rate_limit_service.py:93-104`, `135-166`, `168-202`

Flow:
1. `_ensure_bucket(user_key)` — `INSERT ON CONFLICT DO NOTHING` + `flush()`
2. `_ensure_bucket(ip_key)` — same
3. `_transact()` — locks rows + computes + updates

The `ON CONFLICT DO NOTHING` is fine for creation; but between (2) and (3) there's no lock held. If two concurrent requests for the same `user_id` both pass step 1+2 (no-ops on existing row) and then both arrive at step 3, Postgres `SELECT FOR UPDATE` serializes — good. But: **`_transact` calls `await self._db.flush()` at the end, NOT `await self._db.commit()`**. Whether the locks survive until the outer FastAPI request's session commits depends on the session config (autobegin / explicit commit). On the Postgres production path, `messages.py:162` calls `_check_rate_limit_or_429` which awaits the flush; subsequent code does NOT commit before LLM. If the LLM call takes 5s, **the row lock is held for the whole 5s** — DB pool exhaustion under load.

Trace: `messages.py` → `RateLimitService(db).check_and_consume` → `_transact` → `_lock_row("FOR UPDATE")` → flush only → continues into LLM → finally `await persist_assistant_message` + commit.

For production this is the difference between "rate limit takes 20ms" and "rate limit blocks the connection for 5s while LLM runs". Suggest: commit the rate-limit transaction in a sub-session, OR use a savepoint, OR drop FOR UPDATE and rely on optimistic update with WHERE-clause check.

Severity: critical — performance + DB pool risk under any real load. Spec calls out "<20ms" target.

---

## High (8)

### H1. Rate-limit failure mode silently fails-open
`app/services/chat/rate_limit_service.py:101-104`

```python
except Exception as exc:  # noqa: BLE001
    logger.warning("rate_limit error for user=%s ip=%s: %s", user_id, ip, exc)
    return RateLimitResult(allowed=True)
```

Step 1A report explicitly deferred this decision to Step 2; Step 2 did not address it. A single DB blip or schema mismatch silently disables the entire rate-limit subsystem with only a `warning`-level log. Attackers can poison the bucket row (e.g., set `tokens=NaN` via a SQL injection elsewhere) to force the lookup into an exception path and bypass limits forever.

Decision needed:
- **Fail-open** (current): document the risk; add metrics/alerting.
- **Fail-closed**: catch only known DB errors (asyncpg specific), let unknown exceptions return `allowed=False, reason="rate_limit_unavailable"`.

I'd argue fail-closed for unknown exceptions + fail-open for `OperationalError` (connection drops). Currently it's fail-open for everything.

---

### H2. `cleanup_semantic_cache.run` shares one session for both cleanups + a single commit
`app/jobs/cleanup_semantic_cache.py:21-40`

Single `async with async_session_factory() as db` containing two `cleanup_expired()` calls. If `sem_svc.cleanup_expired()` succeeds (deletes 1000 rows) but `pc_svc.cleanup_expired()` raises, the implicit rollback wipes the semantic_cache deletes too. Either:
- Two separate sessions + two commits, OR
- Wrap each `cleanup_expired` in a savepoint with `try/except`, OR
- Document that all-or-nothing is the desired semantics (it probably isn't for nightly cleanup).

---

### H3. `_ensure_bucket` is called every request even when bucket exists
`app/services/chat/rate_limit_service.py:95-96`

Every `check_and_consume` issues `INSERT ON CONFLICT DO NOTHING` for both buckets. On a hot path (every chat message) this is two extra writes-attempt + index lookups even though 99.9% of the time the row exists. Re-order:
1. Try `_transact` first (assumes row exists).
2. If `_lock_row` raises `NoResultFound`, then `_ensure_bucket` + retry.

Saves 2 SQL writes per chat message at scale.

---

### H4. `PromptCacheService.maybe_create` race with concurrent threshold trips
`app/services/chat/prompt_cache_service.py:201-242`

`_HitCounter` is in-process and not atomic with the DB INSERT. Two workers/threads can both hit threshold within milliseconds and both call `client.caches.create(…)` (Gemini API call). The duplicate-key `IntegrityError` correctly rolls back the second INSERT, but the second Gemini cache (now orphaned in Gemini's storage) is never cleaned up. Costs: 1 wasted cache token allocation + the orphan lives until Gemini TTL expires.

Mitigation: before calling Gemini in `maybe_create`, do a quick SELECT for an existing live handle by `cache_key` and return early. Optional: trust `get_live_handle` to be called first (currently is, by both `messages.py` and `_stream_generator.py`). Just add a comment that the SELECT-then-INSERT race is bounded.

---

### H5. `RateLimitService._update_row` decrements 1 unconditionally — but tokens started as floats with NUMERIC(10,2)
`app/services/chat/rate_limit_service.py:199-200`, `229-258`

`tokens - 1` for `tokens=1.0` → `0.00`. For `tokens=1.05` → `0.05`. Token is stored as NUMERIC(10,2) with 2 decimal places. After `round(new_tokens, 2)` plus float→str conversion, `tokens=0.05` is stored. Then `_apply_refill` reads it back as `float("0.05") = 0.05` — OK. But `_check_bucket` requires `tokens >= 1.0` to allow — `tokens=0.05` correctly fails. No correctness issue, but the `str(round(new_tokens, 2))` round-trip is brittle if anyone changes precision. Recommend: use `Decimal` end-to-end OR document the NUMERIC(10,2) coupling.

---

### H6. `messages.py` Step 2 spec line 167 says "FastAPI `Depends(rate_limit_check)` before quota check" — implementation reverses it
`app/routers/chat/messages.py:159-162`

Plan spec: rate limit first, then quota. Implementation: quota first (to get the tier), then rate limit. Step 2 backend report explicitly notes this and justifies it (rate limit needs `tier`). Acceptable trade-off — but should be reflected in the plan markdown so future readers don't think it's a deviation.

Either update `phase-06-cache-rate-limit.md` step 9 to "After quota check (which provides tier), call rate limit", OR move rate limit to before quota and use a default tier ("free") for the rate-limit check. I'd update the plan; current implementation is correct.

---

### H7. Stream cache-hit yields entire answer in one delta — not a stream
`app/routers/chat/_stream_generator.py:96`

```python
yield sse_event("delta", {"token": cached.answer})
```

For a 500-char Vietnamese answer, the FE sees one giant token frame instead of a streamed feel. Acceptable for v1 (KISS), but UX-inconsistent with LLM streaming. Consider chunking by sentence or fixed-size for parity. Document if intentional.

---

### H8. `useRateLimitCountdown` interval callback uses stale `state.secondsLeft` only via functional updater — OK; but `state.active` check inside `setState` is correct
`Numerology-Landing-Page/src/modules/chat/hooks/use-rate-limit-countdown.ts:48-57, 63-67`

The `useEffect` at line 63 watches `state.active` and stops the interval when it flips to false. But the interval callback at line 48 also sets `active: false` directly. There's a 1-tick window where `setState((prev) => …)` returns `active: false` but the next interval tick (1s later) is already queued and runs once more before the effect cleanup runs. Tick fires `setState((prev) => { const next = 0 - 1 = -1; … return active: false, secondsLeft: 0, reason: null })` — sets state to same shape; React bails on identical state. No visible bug, but the redundant tick is wasteful. Suggest: clear the interval inside the functional updater when `next <= 0`:

```ts
intervalRef.current = setInterval(() => {
  setState((prev) => {
    const next = prev.secondsLeft - 1
    if (next <= 0) {
      stopInterval()  // stops via ref capture
      return { active: false, secondsLeft: 0, reason: null }
    }
    return { ...prev, secondsLeft: next }
  })
}, 1000)
```

Minor; cleanup-on-unmount IS correctly wired (`useEffect` line 70-74).

---

## Medium (10)

### M1. Files exceed 200-LOC guideline
- `app/routers/chat/messages.py`: 327 (target ≤200). Split the cache-hit path into `app/services/chat/chat_turn.py` helper (`serve_from_cache(...)`).
- `app/services/chat/prompt_cache_service.py`: 343. Counter logic + Gemini client could be split.
- `app/routers/chat/_stream_generator.py`: 221. Slightly over — acceptable.
- `app/services/chat/rate_limit_service.py`: 309. Helpers `_apply_refill`, `_check_bucket` could move to `rate_limit_math.py`.
- `app/services/chat/llm_service.py`: 244. Over by 22%.

Per `CLAUDE.md` modularization rule, refactor in a follow-up phase or document the deviation.

### M2. `cache_key` truncated to 64 hex chars but column is VARCHAR(200)
`app/services/chat/prompt_cache_service.py:153`, `alembic/versions/0013_cache_and_rate_limit.py:113`

`hashlib.sha256().hexdigest()[:64]` returns full 64-char hex. Column is `VARCHAR(200)` for headroom — no truncation actually occurs since `[:64]` of a 64-char string is the same. Either tighten column to `VARCHAR(64)` (saves storage + improves index efficiency) or remove the `[:64]` for symmetry. Cosmetic.

### M3. HNSW index requires pgvector ≥ 0.5.0 — undocumented
`alembic/versions/0013_cache_and_rate_limit.py:74-77`

Plan deps don't pin pgvector version. Staging with pgvector < 0.5.0 will fail migration silently. Document in migration docstring or README. Add a check in `upgrade()`:
```python
op.execute("DO $$ BEGIN IF (SELECT extversion FROM pg_extension WHERE extname='vector') < '0.5.0' THEN RAISE EXCEPTION 'pgvector >= 0.5.0 required for HNSW'; END IF; END $$;")
```

### M4. `semantic_cache.insert` after `assistant_message` persist — what about empty/no-info answers?
`app/routers/chat/messages.py:247-253`, `_stream_generator.py:165-172`

The canonical no-info path returns BEFORE reaching insert (line 168 in messages.py, line 84 in stream). Good. But if LLM returns "Tôi không có đủ thông tin để trả lời câu hỏi này." (matching NO_INFO_VI as a near-string answer), the cache stores it. Subsequent semantically-similar queries hit the cache + receive no-info forever — even after KB is updated. Recommend:
```python
if NO_INFO_VI in resp.text:
    logger.info("skipping cache insert for no-info response")
else:
    await semantic_cache.insert(...)
```

### M5. `semantic_cache.insert` fire-and-forget pattern — verify it doesn't share txn with assistant message
`app/routers/chat/messages.py:247-253`

The `insert` calls `self._db.flush()` (line 147 in service). On the messages.py path, the assistant message is persisted at line 255 — same session, same uncommitted txn. If `flush()` in `insert` fails (e.g., pgvector cast issue), it rolls back the assistant insert too. The `try/except` catches the error but the SQLAlchemy session may be in an aborted state requiring `rollback()` before further use. After the failed insert, line 255's `persist_assistant_message` would raise `InvalidRequestError: This Session's transaction has been rolled back due to a previous exception during flush`.

Fix: use a separate session for the cache insert (fire-and-forget on different connection). OR call `await self._db.rollback()` in the except block — but that wipes the user_msg insert. Best: use `async_session_factory()` for a fresh session in `insert()`. Critical only if Postgres flush errors happen in practice; SQLite tests don't reproduce.

### M6. No test verifies "cache-hit user is also rate-limit-checked"
`tests/routers/chat/test_messages.py`, `test_stream_endpoint.py`

Rate-limit and semantic-cache tests are independent. Suggest one test: rate-limited user with a cached query — expect 429 not from_cache. Confirms ordering.

### M7. Magic numbers checked — all settings-backed
Verified `0.92` → `settings.semantic_cache_threshold`, `24h` → `settings.semantic_cache_ttl_hours`, `5` → `settings.prompt_cache_hit_threshold`, `3600s` → `settings.prompt_cache_ttl_seconds`. Good.

### M8. `_HitCounter` global state pollutes between tests
`app/services/chat/prompt_cache_service.py:61-83`

`_hit_counts: dict[str, int] = defaultdict(int)` is module-global. Tests reset their keys with `_HitCounter.reset(cache_key)` but the dict grows unboundedly across the test suite. Production: same issue — long-running process accumulates entries for distinct cache_keys. Eviction strategy: trim entries when len > 1000.

### M9. `RateLimitConfig.tier` lookup for "free" vs "flash"
`app/services/chat/rate_limit_service.py:111-122`

`tier == "pro"` returns pro config; else returns free. In `messages.py:160`, `tier = decision.tier or "flash"`. The "flash" string is never explicitly handled — it falls through to free config. Spec uses "free" and "pro" (line 164 of plan). The QuotaService apparently returns "flash" or "pro". Document the mapping: "flash → free tier limits, pro → pro tier limits". Or rename `decision.tier` to align.

### M10. Stream cache-hit `from_cache` field on `done` event is undocumented
`app/routers/chat/_stream_generator.py:117-124`

SSE schema in `messages.py:299-307` docstring lists `done` event keys as `message_id`, `input_tokens`, `output_tokens`, `model_used`. The `from_cache=True` (`_stream_generator.py:122`) is added only on cache-hit. Document this in the schema OR remove it from the `done` event and check `model_used == "cache"` on FE.

---

## Low / Nits (8)

- `app/services/chat/semantic_cache_service.py:30-32`: `datetime.utcnow()` is deprecated in Python 3.12+. Use `datetime.now(timezone.utc).replace(tzinfo=None)` if naive UTC is required.
- `app/services/chat/rate_limit_service.py:32`: `logger = logging.getLogger(__name__)` defined but only `warning` is called. Fine.
- `app/services/chat/rate_limit_service.py:304`: `from datetime import timedelta` should be at top of module — already imported on line 21. Local import is dead/redundant; remove.
- `app/services/chat/prompt_cache_service.py:151-153`: `compute_key` docstring doesn't mention sorting behaviour. Already covered in test `test_compute_key_chunk_id_order_invariant` but worth a line.
- `app/routers/chat/messages.py:115-116`: `_build_prompt_cache_svc` is only called once — inline the lambda or call `PromptCacheService(...)` directly.
- `alembic/versions/0013_cache_and_rate_limit.py:135`: drop index `prompt_cache_handles_cache_key_idx`, but the table also has a UNIQUE constraint on `cache_key` (line 113) which implicitly creates an index. Either the unique=True or the index is redundant. The DROP works either way but DDL is messy.
- `app/utils/network.py:11`: docstring lists Nginx's `X-Real-IP` but Cloudflare's standard header is `CF-Connecting-IP`. `settings.trusted_proxy_mode` exists for this — but `get_client_ip` ignores it. If `trusted_proxy_mode == "cloudflare"`, should prefer `CF-Connecting-IP`.
- `Numerology-Landing-Page/.../use-rate-limit-countdown.ts:45-46`: `if (retryAfter <= 0) return` — a server-sent `retry_after: 0` silently disables the hint. Defensive: still set state with `active: true, secondsLeft: 1` for at least a brief visual.

---

## Strengths

1. **Pipeline ordering is explicit and consistent** — both sync and stream paths follow the same numbered steps; documented in `messages.py` and `_stream_generator.py` module docstrings.
2. **Two-bucket atomicity is correctly implemented** — `_transact` evaluates BOTH bucket states before either UPDATE fires (`rate_limit_service.py:186-200`). User pass + IP fail returns early without touching user row. Test `test_both_buckets_must_pass_user_pass_ip_fail_no_user_consume` proves this.
3. **`cached_content` SDK kwarg confirmed correct** — verified `google-genai 1.47.0` `GenerateContentConfig.model_fields` contains `cached_content`. The `cfg_kwargs[...] = cached_content` dict-expansion pattern avoids passing `None` which can confuse the SDK.
4. **Cache-hit path persists assistant message correctly** — both sync (`messages.py:178`) and stream (`_stream_generator.py:99`) call `persist_assistant_message(model_used="cache")` so conversation history stays consistent. Quota decrement is also wired (line 188 and 110 respectively). C1 from the scoping doc is satisfied.
5. **Test coverage of new endpoints** — autouse fixture stubs semantic cache globally to keep legacy tests passing without touching EmbeddingService. Cache-hit, prompt-cache, rate-limit, and quota-exhausted paths each have dedicated test classes.
6. **`_apply_refill` and `_check_bucket` are pure functions** — testable without DB, covered by 4 standalone unit tests.
7. **`get_live_handle` refreshes TTL on hit** — keeps hot keys alive; verified by `test_get_live_handle_refreshes_expires_at_on_hit`.
8. **Prompt cache integrity error handling** — concurrent INSERT race correctly caught (`prompt_cache_service.py:238-242`), rolled back, returns None.
9. **Frontend ref-stabilisation pattern reused** — `onRateLimitedRef` mirrors the existing `onQuotaExceededRef` pattern; no new conventions introduced.
10. **Cleanup job tested with mocked session factory** — 5 tests cover empty tables, expired-only deletion, result shape, and commit invocation.

---

## Test coverage gaps

- **No test for "rate-limited user with cached query"** (M6). Tests cache-hit and rate-limit independently — never together.
- **No test for KB sync → prompt cache invalidation** chain. C1's broad-strokes behaviour is critical but no integration test verifies that a numerology row UPDATE results in `prompt_cache_handles` DELETE.
- **No test for `_ensure_bucket` race on first request**. Concurrent first-ever requests for the same user create two `INSERT ON CONFLICT DO NOTHING`s; only one wins. Behaviour is correct but untested.
- **No test for `daily_reset_date` timezone edge case** (C2). At 23:59 UTC the math is sensitive.
- **No test for `semantic_cache.insert` failure path on transactional rollback** (M5). The try/except catches the exception but doesn't restore the session.
- **`test_concurrent_consume_double_call_only_one_or_both_succeed` (line 338)** is a no-op assertion — `assert successes >= 0` always passes. Either skip the test on SQLite or rewrite for Postgres-only.
- **No test for `LlmService` `cached_content` parameter being honored in `_call`** — the integration tests mock `LlmService.generate`, never exercising the real `cfg_kwargs` expansion. Add a unit test that calls `_sync()` with a mock client and asserts `cached_content="caches/foo"` was on the config.

---

## Unresolved questions

1. **C1 fix scope**: implement content-hash short-circuit in `_replace_chunks` (cleanest), or gate `invalidate_for_chunks_sync` on `action=='delete'`? Former is more correct; latter is faster to ship. Lead's call.
2. **C2 timezone semantics**: are daily caps UTC or Asia/Bangkok? Spec is silent. Affects both `_check_bucket.daily_cap` retry calc AND the scheduler at 03:15. Need a one-line decision.
3. **C3 lock duration**: is the current "lock held until end-of-request" intentional (for atomicity) or accidental (because `_transact` only flushes)? If intentional, document the throughput ceiling. If accidental, refactor to commit the rate-limit row immediately.
4. **H1 fail-open vs fail-closed**: launch decision needed. Recommendation is fail-closed for unknown exceptions, fail-open for connection errors.
5. **M4 no-info caching**: is it intentional to cache the canonical NO_INFO answer? It bloats the cache and serves stale answers after KB updates.
6. **Frontend SSE `rate_limited` branch is partly dead code**: backend `messages.py:75-93` only emits HTTP 429, never SSE. The FE's `handleFrame` rate_limited path (`use-chat-stream.ts:239-252`) cannot fire today. Either remove the FE branch (YAGNI) or add an SSE rate_limited path on backend for in-stream limits (not currently a use case).
