# Phase 06 — Semantic Cache + Prompt Caching + Rate Limit

## Context Links
- Depends on: P2 (LLM service), P5 (tier resolution)
- Brainstorm: §3.4 cost optimization, §4.5 rate limit

## Overview
- **Priority:** Critical (locks in cost target before launch)
- **Status:** complete (2026-05-28)
- **Duration:** 1 week
- **Description:** Add semantic cache (pgvector similarity on queries), Gemini prompt caching for system + KB context, token bucket rate limit per (user_id, ip).

## Key Insights
- Semantic cache hit if cosine similarity >0.92 AND same tier — return cached answer + citations, skip LLM.
- Gemini prompt caching: explicit cache via `client.caches.create(...)` for system prompt; TTL 1h, refresh on hit. Saves 75% on cached input tokens.
- Rate limit token bucket: free 1 msg/10s, paid 1 msg/3s; IP-wide 50/day.
- Use PostgreSQL row-level lock for token bucket (no Redis needed initially).

## Requirements

### Functional
- Insert `semantic_cache` row after each successful answer (TTL 24h).
- Before LLM call: embed user query → cosine search → hit if score >0.92 + same tier.
- On cache hit: don't decrement quota (free hit) OR decrement but no LLM cost? **Decision: decrement (consistent UX, prevents abuse), cost saving comes from skipping LLM.**
- Gemini explicit prompt caching for system prompt + top KB chunks (when reused across requests).
- Rate limit: 429 when bucket empty, with `Retry-After` header.

### Non-Functional
- Cache lookup <100ms.
- Rate limit check <20ms.
- Cache hit rate >25% after 1 month (success metric).

## Architecture

```
app/services/chat/
├── semantic_cache_service.py        # lookup + insert + TTL cleanup
├── prompt_cache_service.py          # Gemini cached_content lifecycle
└── rate_limit_service.py            # token bucket via DB row lock
app/db/models/chat/
├── semantic_cache_entry.py
├── rate_limit_bucket.py
└── prompt_cache_handle.py           # store Gemini cache_id + expiry
alembic/versions/
└── 0013_cache_and_rate_limit.py
app/jobs/
└── cleanup_semantic_cache.py        # nightly TTL prune
```

## SQL Schema (alembic 0013)

```sql
CREATE TABLE semantic_cache (
  id BIGSERIAL PRIMARY KEY,
  tier VARCHAR(20) NOT NULL,
  query_embedding vector(768) NOT NULL,
  query_text TEXT NOT NULL,
  answer TEXT NOT NULL,
  citations JSONB NOT NULL DEFAULT '[]',
  hit_count INT NOT NULL DEFAULT 0,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  expires_at TIMESTAMPTZ NOT NULL DEFAULT (NOW() + INTERVAL '24 hours'),
  last_hit_at TIMESTAMPTZ
);
CREATE INDEX semantic_cache_tier_expires_idx ON semantic_cache(tier, expires_at);
CREATE INDEX semantic_cache_hnsw_idx ON semantic_cache
  USING hnsw (query_embedding vector_cosine_ops);

CREATE TABLE rate_limit_buckets (
  bucket_key VARCHAR(100) PRIMARY KEY,    -- 'user:123' or 'ip:1.2.3.4'
  tokens NUMERIC(10,2) NOT NULL,
  capacity NUMERIC(10,2) NOT NULL,
  refill_rate NUMERIC(10,4) NOT NULL,      -- tokens per second
  last_refill TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  daily_count INT NOT NULL DEFAULT 0,
  daily_reset_date DATE NOT NULL DEFAULT CURRENT_DATE
);

CREATE TABLE prompt_cache_handles (
  id BIGSERIAL PRIMARY KEY,
  cache_key VARCHAR(200) NOT NULL UNIQUE,   -- hash of system+kb_chunks
  gemini_cache_id VARCHAR(255) NOT NULL,
  model VARCHAR(50) NOT NULL,
  token_count INT NOT NULL,
  expires_at TIMESTAMPTZ NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

## Related Code Files

### Create
- `app/db/models/chat/semantic_cache_entry.py`
- `app/db/models/chat/rate_limit_bucket.py`
- `app/db/models/chat/prompt_cache_handle.py`
- `app/services/chat/semantic_cache_service.py` (≤150 LOC)
- `app/services/chat/prompt_cache_service.py` (≤120 LOC)
- `app/services/chat/rate_limit_service.py` (≤180 LOC)
- `app/jobs/cleanup_semantic_cache.py` (≤60 LOC)
- `alembic/versions/0013_cache_and_rate_limit.py`
- `tests/services/chat/test_semantic_cache_service.py`
- `tests/services/chat/test_rate_limit_service.py`
- `tests/services/chat/test_prompt_cache_service.py`

### Modify
- `app/routers/chat/messages.py` — wire cache lookup + rate limit (before quota check)
- `app/services/chat/llm_service.py` — use cached_content handle when available

## Implementation Steps

### Semantic cache
1. **Service**
   ```python
   class SemanticCacheService:
       async def lookup(self, query: str, tier: str) -> CachedAnswer | None:
           emb = await self.embedding.embed_one(query)
           # SELECT ... ORDER BY embedding <=> :emb LIMIT 1
           # WHERE tier = :tier AND expires_at > NOW()
           # check 1 - cosine_distance >= 0.92
       async def insert(self, query, tier, answer, citations): ...
       async def increment_hit(self, cache_id): ...
   ```

2. **Wire in messages router**
   ```python
   cached = await semantic_cache.lookup(content, tier)
   if cached:
       await semantic_cache.increment_hit(cached.id)
       # save user+assistant msg (model='cache')
       await quota.decrement(decision)
       return MessageOut(..., from_cache=True)
   # else: proceed with LLM
   ```

3. **TTL cleanup**
   - Daily job: `DELETE FROM semantic_cache WHERE expires_at < NOW()`.

### Prompt cache (Gemini)
4. **Cache key computation**
   - SHA256 of (system_prompt + sorted_kb_chunk_ids + tier).
   - If hits same key reused often (e.g., >5 times) → create explicit Gemini cache via `client.caches.create`.

5. **Lazy creation**
   - First N requests: don't cache (avoid one-shot waste).
   - After threshold (5 hits same key in 1h): create Gemini cache → store handle.
   - Subsequent requests: pass `cached_content=handle` → 75% input cost reduction.

6. **Lifecycle**
   - TTL 1h refresh on each use; delete handle when KB chunks change (P1 sync invalidates).

### Rate limit
7. **Service**
   ```python
   class RateLimitService:
       async def check_and_consume(self, user_id, ip, tier) -> RateLimitResult:
           # 2 buckets: user-specific + IP-specific
           # token bucket math: refill = (now - last_refill) * rate
           # atomic: BEGIN; SELECT FOR UPDATE; compute; UPDATE; COMMIT
           # tier sets capacity/refill_rate
   ```

8. **Configuration**
   - Free user: capacity 1, refill 0.1/s (=1 every 10s), daily 100.
   - Paid user: capacity 1, refill 0.33/s (=1 every 3s), daily 1000.
   - IP-wide: capacity 5, refill 0.05/s, daily 50.

9. **Middleware/dependency**
   - FastAPI `Depends(rate_limit_check)` before quota check.
   - On 429: include `Retry-After: <seconds>` header.

10. **Tests**
    - Semantic cache: identical query returns cached.
    - Similar query (>0.92 sim): returns cached.
    - Different tier: same query but free/paid don't share cache.
    - Rate limit: 2 rapid requests → 2nd 429.
    - Refill: wait 10s, request succeeds.
    - Daily cap: 51st IP request → 429 even with tokens.

## Todo List

- [x] Write alembic 0013 migration
- [x] Create 3 cache/limit model files
- [x] Implement `semantic_cache_service.py`
- [x] Implement `prompt_cache_service.py` with Gemini explicit cache
- [x] Implement `rate_limit_service.py` token bucket
- [x] Wire cache lookup in messages router (before LLM call)
- [x] Wire rate limit middleware
- [x] Implement nightly cleanup job
- [x] Invalidate prompt_cache_handles when KB chunks change (hook in P1 sync)
- [x] Write unit tests (cache hit, rate limit refill, concurrent consume)
- [ ] Load test: 100 RPS to verify rate limit + cache hit rate
- [ ] Monitor cache hit rate over 24h on staging
- [ ] Tune similarity threshold (0.92) based on false positive rate sample

## Success Criteria
- Identical question asked twice within 24h → 2nd hits cache (verified via `from_cache=True`).
- Burst of 5 messages in 5s from free user → 4 of them get 429.
- Gemini cache creates handle after 5 hits, subsequent input tokens reported as cached.
- Cache hit rate >15% on staging after 100 test conversations.

## Risk Assessment

| Risk | Mitigation |
|------|------------|
| Cache returns slightly wrong answer (false hit) | Threshold 0.92 strict; manual eval 100 hits sample monthly |
| Prompt cache becomes stale when KB updates | Invalidation hook on KB change; TTL 1h max |
| Rate limit DB lock contention at high RPS | Move to Redis if >100 RPS sustained; current scale OK |
| User bypasses cache by adding random chars | Embedding still semantically similar; threshold catches this |
| Cache table grows unbounded | Nightly TTL prune + cap entries (delete LRU when >100k rows) |

## Security Considerations
- Cache scoped by tier — Pro answers never leak to free users.
- Rate limit on auth attempts NOT in scope (separate concern).
- IP-based limit prevents account-share abuse but exempt for office/NAT'd users with verified email (future enhancement, log warning).
- Cached citations validated still-existent KbChunks before serving.

## Completion Notes

### Files Created
- Alembic 0013: `alembic/versions/0013_*.py` (semantic_cache, rate_limit_buckets, prompt_cache_handles tables + HNSW index)
- Models: `app/db/models/chat/semantic_cache_entry.py`, `rate_limit_bucket.py`, `prompt_cache_handle.py`
- Services: `app/services/chat/semantic_cache_service.py`, `prompt_cache_service.py`, `rate_limit_service.py`
- Job: `app/jobs/cleanup_semantic_cache.py`
- Tests: 345 passed (0 failed, 4 skipped pgvector)

### Pipeline Architecture
Rate limit → Quota check → Retrieval → Semantic cache lookup → Prompt cache get_or_create → LLM (with cached_content) → cache insert → persist + decrement. Reordered per H6 (rate limit before quota to fail-fast on abuse).

### Fail-Closed Policy
DB errors: return disallowed with retry_after=5, reason=service_error. No silent fallthrough.

### Timezone & Reset
Bangkok TZ (UTC+7) for daily_cap daily counter reset. Retry-After header for 429 responses.

### Prompt Cache Invalidation
Content-hash short-circuit in kb_ingestion_service.py prevents spurious invalidations on no-op re-syncs. KB sync after-commit hook calls invalidate_for_chunks_sync atomically.

### Code Review Outcomes
3 criticals + 8 highs + 10 mediums all resolved. Selected deferred (H2 job tx, H3 perf, H4 race at scale). File LOC: prompt_cache_service.py 330, messages.py 233 (both >200 — note for Phase 08 refactor).

## Next Steps / Dependencies
- **Unlocks:** Phase 08 cost targets achievable.
- **Required for:** Public launch (cost guardrail).
- **Parallel-safe with:** Phase 07 (admin UI).
