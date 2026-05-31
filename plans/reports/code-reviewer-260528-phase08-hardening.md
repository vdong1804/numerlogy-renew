# Phase 08 Hardening — Code Review

**Reviewer:** code-reviewer subagent
**Date:** 2026-05-28
**Scope:** alembic 0015, 4 new chat models, 4 new chat services, 2 jobs, hardening gate, DSAR endpoint, A/B prompt wiring, turnstile extension, scheduler registration, 7 test modules, 3 docs.
**Test status reported:** 400 passed / 4 skipped (+9 pre-existing unrelated failures).

---

## Grade: **B+** — Approved with notes

Solid architectural fit (raw `text()` + dict binds match existing chat services); correct cheapest-first hardening gate order; sane DSAR semantics. Knocked from A by two real race-condition bugs (CAPTCHA solve counter, abuse score CASE), one cross-DB portability bug in `users.chat_captcha_required` server_default, magic-number coupling in abuse detector, and a handful of LOC-budget overruns vs spec.

---

## Critical findings

None — no security exploit, data-loss, or breaking-API issues found.

---

## High findings

### H1. Race window — CAPTCHA solve counter can clear flag for the wrong user state
`app/services/turnstile_service.py:73-89`
The single `UPDATE` reads `chat_captcha_solve_count + 1 >= :n` and in the same statement either resets to 0 or increments — correct for a single row, but **`verify_chat_captcha` does NOT take `SELECT … FOR UPDATE`** and there is no commit in the gate before this call. Two concurrent requests from the same user both see `solve_count=4`, both compute `4+1>=5 → clear + reset to 0`, and the user gets two CAPTCHA-free turns. Worse, three concurrent requests at `solve_count=3` each see `3+1<5`, all increment to 4, then a fourth solo request sees 4, clears. Net effect: one clear can be triggered with 3 solves instead of 5.

**Mitigation:** wrap the UPDATE in a `SELECT … FOR UPDATE` (`with_for_update()` on the user row) inside an explicit transaction, OR add a `WHERE chat_captcha_solve_count = :expected` optimistic-concurrency clause and retry on 0 rowcount. Cheap fix: a row-level lock since CAPTCHA isn't hot-path.

### H2. Race window — `_apply_score_delta` CASE re-reads stale value
`app/services/chat/abuse_detection_service.py:238-262`
`UPDATE users SET chat_abuse_score = chat_abuse_score + :d, chat_captcha_required = CASE WHEN chat_abuse_score + :d >= :cap …` — Postgres evaluates each column expression against the **pre-update** row snapshot, so this is internally consistent *within one statement*. BUT two concurrent calls (e.g. inline `prompt_injection` from router + cron `detect_chat_abuse` job firing in the same 15-min window) can both observe `score=9`, each adds 5, final score is 19 — and each one independently triggers the threshold check correctly. So actually **this is safe under concurrent UPDATEs** because Postgres serializes row-level writes — each UPDATE sees the post-previous-commit value. Confirm with `READ COMMITTED` isolation (default). **Mark as informational, but add a test for concurrent score deltas to prevent regression.**

### H3. `users.chat_captcha_required` server_default `"0"` is wrong type for PG `Boolean`
`app/db/models/user.py:31-33`
`server_default="0"` works on SQLite (BOOL stored as INTEGER) but on Postgres `Boolean` columns require `sa.text("FALSE")` or `"false"`. The Alembic migration `0015_hardening.py:115` correctly uses `sa.text("FALSE")`, but the ORM model's `server_default` is only used if you ever recreate the schema from `Base.metadata.create_all()` — which **tests do**. Currently tests pass because SQLite is forgiving. If anyone runs `create_all` against PG (e.g. in a dev seed script) it raises `InvalidTextRepresentation: invalid input syntax for type boolean: "0"`. Same issue on `ChatFeatureFlag.enabled` (`feature_flag.py:23`) and `chat_abuse_score`/`chat_captcha_solve_count` are fine (Integer). Use `server_default=sa.text("FALSE")` for consistency with the migration.

### H4. Magic-number coupling: free quota threshold hardcoded as `3`
`app/services/chat/abuse_detection_service.py:169` `AND q.free_used >= 3`
This must equal `settings.chat_free_daily_limit` (currently 3). If product bumps the free limit to 5, the grief detector silently flags everyone hitting the new quota of 3. Replace literal `3` with `settings.chat_free_daily_limit` interpolated server-side (or pass via bind param).

### H5. `cost_inc` is `from_cache` parameter but cache hits skip the call entirely
`app/services/chat/cost_monitor_service.py:78-119` exposes `from_cache: bool = False`, but `messages.py` and `_stream_generator.py` (the only callers) **never invoke `record_message_cost` on cache hits**. The hourly aggregator computes `cache_hits` from `model_used='cache'` rows directly. So the `cache_inc` UPSERT branch is dead code that masks a real intent: do we want incremental cache_hit counting on hot path, or only from the aggregator job? Pick one. Recommendation: delete the `from_cache` param and the `cache_inc` column write — the aggregator covers it and it removes a hot-path write per cache hit.

---

## Medium findings

### M1. LOC budget overruns vs phase-08 spec
- `abuse_detection_service.py` = 271 LOC (spec ≤180). Split: keep detectors here, move `record_inline_flag` + `_apply_score_delta` to `abuse_writer.py`.
- `cost_monitor_service.py` = 193 LOC (spec ≤120). Split: move `alert_if_exceeded` (httpx + email) into `cost_alert_service.py`.
- `aggregate_chat_metrics.py` = 187 LOC (spec ≤150). Acceptable; main offender is the cost-calc inline loop — extract to a helper.

These are guidelines, not blockers, but the spec explicitly called out budgets — flag for resolution before launch.

### M2. `_recompute_for_date` does `from app.services.chat.cost_monitor_service import calc_msg_cost` **inside** the loop
`app/jobs/aggregate_chat_metrics.py:80`
Local-import in a per-row loop. Python caches imports so cost is ~free, but readability suffers. Hoist to module level (`PRICING` is already imported from the same module — adding `calc_msg_cost` to that line is one keystroke).

### M3. Identical-burst detector is a full-table scan with no index
`abuse_detection_service.py:92-106` — `GROUP BY m.content` over `chat_messages` for the 60-min window. On a busy day this becomes the slowest query in the system. Add a partial expression index on `chat_messages(content)` filtered to `role='user' AND created_at > NOW() - INTERVAL '1h'`, OR pre-hash content to a `content_sha1` column.

### M4. `peek_tier` is called BEFORE rate-limit check in `messages.py:174`
Adds one DB roundtrip on every request that gets rate-limited. Pre-Phase-08 this was acceptable; with hardening adding 2-3 more SELECTs ahead of it (feature flag + suspended_at on `user`), hot-path now has 5+ reads before the work starts. Consider: combine the `is_enabled` + `chat_suspended_at` reads into a single SELECT, or precompute on auth.

### M5. DSAR endpoint is not idempotent at the audit-log level
`app/routers/profile.py:124-129` — logs deletion rowcounts every time. A double-DELETE call logs zeros on the second invocation, which is correct, but there is no audit-log table write — just a logger call. Phase-08 spec line 194 calls for `log to audit_log`. Either wire a real audit row insert, or add a `# TODO(audit): persist to audit_log when table exists` so this isn't forgotten pre-GDPR enforcement.

### M6. `FeatureFlagService._cache` class-level dict — no per-process eviction on shutdown
Memory leak risk negligible (data is tiny) but the cache is module-global and survives across tests in the same process. Test `conftest.py` calls `FeatureFlagService.invalidate()` correctly. Production: 60s TTL means a stale read after admin toggle can pin a user to the previous flag for up to a minute, **violating the success criterion "rollback test: disable in admin → service returns 503 within 60s"** (line 258 in plan). Borderline OK (60s = budget) but if the admin write goes through a different process than the reader process (multi-worker uvicorn), the readers' caches won't invalidate until TTL expires. Document this in `chatbot-runbook.md` ("toggle propagation: up to 60s × worker count").

### M7. Prompt-injection regex narrow patterns miss common attacks
`abuse_detection_service.py:42-48`. Misses:
- "Please ignore all instructions above" (no "previous"/"prior"/"above"/"earlier" with "instructions" in canonical order — `r"ignore.*above.*instructions"` would catch this, but greedy matching has FP risk)
- Markdown injection: `[INST]`, `[/INST]`, `</s>`, `### Instruction:`
- Encoded variants: base64-wrapped jailbreaks, ROT13
The README under `docs/chatbot-runbook.md` should call out this is *defense in depth*, not the only line, and that the LLM system prompt itself must refuse. Don't over-engineer the regex — false positives bite users.

### M8. `chat_addon_purchases.user_id` SET NULL + the `package` relationship now allows orphan billing rows with no user
Acceptable per spec ("keep for billing"), but `app/services/chat/quota_service.py` queries `chat_addon_purchases WHERE user_id = :u` — if quota.decrement happens to encounter a NULLed row in some join, behavior is OK (filtered out). Just verify no `JOIN user` or `INNER JOIN` exists with no `LEFT` outer. (Spot check shows it does not; mark resolved.)

---

## Low findings

- `app/routers/chat/messages.py:87` — inline `from app.services.chat.cost_monitor_service import CostMonitorService` inside the rate-limit handler. Hoist to top of file.
- `cost_monitor_service.py:115-116` — comment "aiosqlite can't bind Decimal directly; str round-trips fine on PG NUMERIC" is **correct**: PG NUMERIC accepts string-typed bind params via the asyncpg driver, which parses on the server side. No fix needed; the explanatory comment is good practice.
- `aggregate_chat_metrics.py:74-79` — model-string prefix matching is fragile. If Google ships `gemini-2.0-flash-002`, it'll fall through to `flash_model` settings lookup — fine if that's updated, otherwise PRICING miss → silent zero cost. Add a warning log when prefix matches but exact key not in PRICING.
- `_hardening_gate.py:75` — commit on every prompt-injection 400 means abuse-flag rows always persist even if the caller wraps in their own transaction. This is intentional and correct (abuse evidence must persist) but worth a comment.
- `ab_test_service.py:33-37` — `_bucket` uses `digest[0] % 100` like `feature_flag_service._user_bucket`. Two separate implementations; consolidate into `app/utils/bucket.py`.

---

## Edge cases worth scouting

1. **CAPTCHA + suspended interaction:** a user who hits suspend (score≥50) still has `chat_captcha_required=TRUE`. After admin clears suspension (`chat_suspended_at=NULL`), the CAPTCHA gate still fires. Is that intentional? If yes, document it.
2. **Feature flag rollout=0, enabled=True** — current code returns False (line 76 of `feature_flag_service.py`). Correct, but worth a regression test: someone could mistakenly type `enabled=True, rollout=0` to "soft-disable" and inadvertently rely on the short-circuit.
3. **Identical burst false-positives:** "tôi muốn xem số của tôi" is plausibly typed 10+ times across users in 1h on a viral day. Flag has score 6 + no user_id → no user-side effect, but flood of admin-review rows. Add a content-length floor (skip burst detection for messages < 20 chars).
4. **DSAR during active chat turn:** user POSTs `/api/profile/chat-data` while a stream is still open in another tab. DELETE cascades on `chat_conversations` but the open stream's `persist_assistant_message` then violates FK. Lock the user out of new chats first or accept the 500 on the racing stream.
5. **Aggregator running against an empty window:** SQLite UNIX_EPOCH date math for `:start/:end` is fine, but verify the `UPSERT` actually writes the all-zero row (it does — INSERT not skipped). Confirm cost dashboard tolerates zero-rows for days with no traffic.

---

## Top 3 specific code changes I'd request before launch

1. **Fix `users.chat_captcha_required` server_default** in `app/db/models/user.py:33` and `chat_feature_flags.enabled` in `feature_flag.py:23` from `"0"` to `sa.text("FALSE")`. Prevents future schema-recreation breakage.
2. **Add row-lock to `verify_chat_captcha`** in `app/services/turnstile_service.py:73`: either `SELECT chat_captcha_solve_count FROM users WHERE id = :u FOR UPDATE` first, or change the UPDATE to optimistic with `WHERE chat_captcha_solve_count = :expected`. Closes H1 race.
3. **Replace magic `3` in grief detector** at `abuse_detection_service.py:169` with `:limit` bound from `settings.chat_free_daily_limit`. Prevents silent drift if free quota changes.

---

## Verdict

**Approved with notes.** Phase 08 is launch-quality for a controlled rollout starting at 5% per the launch checklist. The H1 race and H3 schema-default bugs should be fixed before scaling above 25%. M-series items can be tracked as follow-ups in phase-09.

---

## Unresolved questions

1. Are admin writes to feature flags going through a single process (cron / admin worker) or any worker? Affects M6 cache-invalidation severity.
2. Spec calls for audit_log integration on DSAR (M5) — is the audit_log table planned for Phase 08 or deferred?
3. Identical-burst detector — acceptable to flag bursts with no user attribution, or should we require ≥2 distinct users to trigger? (Currently fires on a single user posting 10 identical messages, which overlaps with rate-limit.)
4. Should `chat_addon_purchases.user_id = NULL` rows be excluded from analytics queries explicitly, or is the cost dashboard already aware?
