# Phase 06 Sync Report — Semantic Cache + Prompt Caching + Rate Limit

**Date:** 2026-05-28  
**Status:** Phase 06 COMPLETE  
**Plan Overview:** 6/8 phases complete; P07, P08 pending

---

## Files Modified

### 1. phase-06-cache-rate-limit.md
- **Status field:** changed pending → complete (2026-05-28)
- **Todo checklist:** 10/13 items checked (3 deferred: load test 100 RPS, monitor cache hit rate 24h, tune similarity threshold)
- **New section:** Completion Notes added with implementation summary

### 2. plan.md
- **Phase 06 row:** status → complete (2026-05-28)
- **Overall status:** changed in-progress (5/8) → in-progress (6/8)
- **Last sync:** 2026-05-28

---

## Phase 06 Implementation Summary

### Backend Infrastructure
1. **Alembic 0013 migration:** semantic_cache, rate_limit_buckets, prompt_cache_handles tables; HNSW index on query_embedding
2. **3 Models:** SemanticCacheEntry, RateLimitBucket, PromptCacheHandle
3. **SemanticCacheService:** pgvector cosine lookup ≥0.92, insert, increment_hit, cleanup_expired; 20 tests + 4 pgvector-skip
4. **RateLimitService:** two-bucket atomic check_and_consume (user + IP), token bucket math, Bangkok TZ for daily_cap reset; 11 config settings
5. **PromptCacheService:** SHA256 cache key, get_live_handle with TTL refresh, lazy maybe_create after 5 in-process hits, invalidate_for_chunks broad-strokes, cleanup_expired; 13 tests
6. **KB sync integration:** after-commit hook calling invalidate_for_chunks_sync; content-hash short-circuit prevents spurious invalidations

### API Integration
- **Pipeline order:** rate limit → quota check → retrieval → semantic cache lookup → prompt cache get_or_create → LLM (with cached_content) → cache insert → persist + decrement
- **Rate limit check:** <20ms via DB row lock (no Redis initially)
- **Cached content:** MessageOut.from_cache field; LlmService cached_content kwarg (confirmed google-genai 1.47.0)
- **IP detection:** get_client_ip helper (X-Real-IP / X-Forwarded-For / client.host)
- **Cleanup job:** semantic_cache TTL prune scheduled 03:15 daily

### Frontend Integration
- **useRateLimitCountdown hook:** 1s tick, cleanup
- **use-chat-stream:** onRateLimited callback (ref-stabilized)
- **ChatLayout:** handleRateLimited → countdown + sonner toast variants (bucket_empty=warning/3s, daily_cap=error/8s)
- **MessageInput:** hint + send button disable while countdown active
- **Dead code removed:** SSE rate_limited branch from use-chat-stream

### Code Review Resolution
- **3 Criticals:** all fixed (content-hash short-circuit, Bangkok TZ, transaction isolation)
- **8 Highs (selected):** rate limit before quota, fail-closed on DB error, stream cache-hit chunking, hook lifecycle, H8 FE tick removed
- **10 Mediums (selected):** skip cache insert for NO_INFO_VI, cache insert own tx, other improvements
- **Deferred (noted, not fixed):** H2 job txn, H3 perf, H4 race at scale, H5 NUMERIC coupling, file LOC overages

### Test Results
- **345 passed, 0 failed, 4 skipped (pgvector on SQLite)**
- Linting clean (ruff + tsc)

---

## Open Follow-Ups (Deferred, Not Critical)

### Code Quality
| ID | Issue | Priority | Notes |
|----|-------|----------|-------|
| H2 | Cleanup job: single txn for both semantic_cache + prompt_cache deletes (all-or-nothing) | high | Low risk; current sequential ok for nightly job |
| H3 | `_ensure_bucket` writes on every hot-path request | high | Perf optimization; monitor in staging (rate limit bucket writes) |
| H4 | `_HitCounter` race causes orphan Gemini caches at scale | high | Multi-worker race; watch when scale >50 RPS |
| H5 | NUMERIC(10,2) coupling in rate_limit_buckets brittle | med | Token math assumes ≤99.99 capacity; works for current tiers |
| M-other | File LOC >200: prompt_cache_service.py (330), messages.py (233) | med | Refactor target Phase 08 |

### Production Validation (Deferred to Phase 07/08)
- Load test: 100 RPS to verify rate limit + cache hit rate (needs live env)
- Monitor cache hit rate over 24h on staging (staging deployment)
- Tune similarity threshold (0.92) based on false positive rate sample (needs production data)

### Architecture Enhancements
- Per-chunk reverse index for invalidate_for_chunks (Phase 08 optimization)
- pgvector version pin in deployment docs (HNSW requires ≥0.5.0)

---

## Phase Status Consistency Check

All 8 phases scanned. No retroactive changes made to P01–P05.

| Phase | Status | Last Verified |
|-------|--------|----------------|
| 01 | complete (2026-05-26) | ✓ |
| 02 | complete (2026-05-26) | ✓ |
| 03 | complete (2026-05-26) | ✓ |
| 04 | complete (2026-05-27) | ✓ |
| 05 | complete (2026-05-28) | ✓ |
| 06 | complete (2026-05-28) | ✓ **UPDATED** |
| 07 | pending | ✓ |
| 08 | pending | ✓ |

---

## Next Phase (P07 Admin Tuning)

Phase 07 is unblocked. No dependencies on P06 cleanup/optimization tasks (those are P08).

---

## Unresolved Questions

1. **H3 perf optimization (bucket writes):** When should we profile _ensure_bucket writes to assess load at scale?
2. **H4 race condition:** Does current `_HitCounter` design require mutex for >50 RPS multi-worker, or is atomic counter OK?
3. **Cache hit rate target in staging:** What sample size = statistical confidence (100 conversations? 1000)?
4. **Similarity threshold tuning:** Should we collect false positive rate sample in P07 or wait for P08 monitoring?
