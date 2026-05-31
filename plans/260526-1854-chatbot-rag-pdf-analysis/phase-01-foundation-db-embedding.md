# Phase 01 — Foundation: DB Schema + Embedding Service + KB Ingestion

## Context Links
- Brainstorm: `../reports/brainstorm-260526-1854-chatbot-pdf-rag.md`
- Existing models: `numerology-api/app/db/models/`
- Existing alembic: `numerology-api/alembic/versions/` (last: 0009)
- Existing services: `numerology-api/app/services/`

## Overview
- **Priority:** Critical (blocks all subsequent phases)
- **Status:** complete (migration applied; only backfill awaits a real GEMINI_API_KEY)
- **Duration:** 2 weeks
- **Description:** Set up pgvector, create chatbot DB schema, build Gemini embedding service, ingest 22 numerology content tables into KB with auto-sync hook.

## Key Insights
- pgvector HNSW index sufficient for <500k chunks (current scope ~100k).
- text-embedding-004 returns 768-dim vectors; cheap ($0.025/M tokens).
- 22 numerology tables share `NumerologyContentMixin` (id, code, value, title, content) → uniform ingestion code path.
- Auto-sync via SQLAlchemy event listener `after_insert/update/delete` on each content model.

## Requirements

### Functional
- Install pgvector extension on dev + production PG16.
- Create 5 new tables: `kb_documents`, `kb_chunks`, `chat_conversations`, `chat_messages`, `chat_quota_usage`.
- Initial migration (alembic `0010_chatbot_foundation.py`).
- `embedding_service.py`: wrap Gemini text-embedding-004 with batching + retry.
- `kb_ingestion_service.py`: chunk text (500 tokens, 50 overlap), embed, upsert.
- `kb_sync.py`: SQLAlchemy event listener — on any numerology content CRUD, re-embed affected rows.
- One-time backfill script `scripts/backfill_kb.py` for existing data.

### Non-Functional
- Backfill 22 tables × avg 9 rows = ~200 rows in <5 min.
- Embedding API errors retry 3× with exponential backoff.
- Each new code file ≤200 LOC (modularize aggressively).

## Architecture

```
app/
├── db/models/chat/
│   ├── __init__.py
│   ├── conversation.py           # ChatConversation
│   ├── message.py                # ChatMessage
│   ├── quota_usage.py            # ChatQuotaUsage
│   ├── kb_document.py            # KbDocument
│   └── kb_chunk.py               # KbChunk (vector column)
├── services/chat/
│   ├── __init__.py
│   ├── embedding_service.py      # Gemini embedding wrapper
│   ├── kb_ingestion_service.py   # chunk + embed + upsert
│   ├── kb_sync.py                # SQLAlchemy event hooks
│   └── chunker.py                # text splitter (token-aware)
├── config.py                     # +GEMINI_API_KEY, +EMBEDDING_MODEL
scripts/
└── backfill_kb.py                # one-shot ingest all numerology tables
alembic/versions/
└── 0010_chatbot_foundation.py
```

## SQL Schema (alembic op.execute snippets)

```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE kb_documents (
  id BIGSERIAL PRIMARY KEY,
  source_type VARCHAR(50) NOT NULL,
  source_ref VARCHAR(255) NOT NULL,
  title VARCHAR(500),
  metadata JSONB NOT NULL DEFAULT '{}',
  created_by BIGINT REFERENCES users(id) ON DELETE SET NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE(source_type, source_ref)
);
CREATE INDEX kb_documents_source_idx ON kb_documents(source_type, source_ref);

CREATE TABLE kb_chunks (
  id BIGSERIAL PRIMARY KEY,
  document_id BIGINT NOT NULL REFERENCES kb_documents(id) ON DELETE CASCADE,
  chunk_index INT NOT NULL,
  content TEXT NOT NULL,
  embedding vector(768) NOT NULL,
  token_count INT NOT NULL,
  metadata JSONB NOT NULL DEFAULT '{}'
);
CREATE INDEX kb_chunks_doc_idx ON kb_chunks(document_id);
CREATE INDEX kb_chunks_hnsw_idx ON kb_chunks
  USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);

CREATE TABLE chat_conversations (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  title VARCHAR(255),
  pdf_context_id BIGINT,    -- FK added in phase 03
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX chat_conversations_user_idx ON chat_conversations(user_id, created_at DESC);

CREATE TABLE chat_messages (
  id BIGSERIAL PRIMARY KEY,
  conversation_id BIGINT NOT NULL REFERENCES chat_conversations(id) ON DELETE CASCADE,
  role VARCHAR(20) NOT NULL,
  content TEXT NOT NULL,
  model_used VARCHAR(50),
  tier VARCHAR(20),
  input_tokens INT DEFAULT 0,
  output_tokens INT DEFAULT 0,
  citations JSONB DEFAULT '[]',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX chat_messages_conv_idx ON chat_messages(conversation_id, created_at);

CREATE TABLE chat_quota_usage (
  user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  date DATE NOT NULL,
  free_used INT NOT NULL DEFAULT 0,
  paid_used INT NOT NULL DEFAULT 0,
  PRIMARY KEY (user_id, date)
);
```

## Related Code Files

### Create
- `app/db/models/chat/__init__.py`
- `app/db/models/chat/conversation.py`
- `app/db/models/chat/message.py`
- `app/db/models/chat/quota_usage.py`
- `app/db/models/chat/kb_document.py`
- `app/db/models/chat/kb_chunk.py`
- `app/services/chat/__init__.py`
- `app/services/chat/embedding_service.py`
- `app/services/chat/kb_ingestion_service.py`
- `app/services/chat/kb_sync.py`
- `app/services/chat/chunker.py`
- `alembic/versions/0010_chatbot_foundation.py`
- `scripts/backfill_kb.py`
- `tests/services/chat/test_embedding_service.py`
- `tests/services/chat/test_kb_ingestion_service.py`
- `tests/services/chat/test_chunker.py`

### Modify
- `app/config.py` — add `GEMINI_API_KEY`, `EMBEDDING_MODEL`, `GEMINI_FLASH_MODEL`, `GEMINI_PRO_MODEL`
- `app/main.py` — register `kb_sync` event listeners on startup
- `app/db/models/__init__.py` — export new models
- `requirements.txt` — add `google-genai`, `pgvector`, `tiktoken` (or Gemini tokenizer)
- `numerology-api/.env.example` — add Gemini key placeholder

## Implementation Steps

1. **Install dependencies**
   - Add to `requirements.txt`: `google-genai>=0.3`, `pgvector>=0.3`, `tiktoken>=0.7`.
   - Run `pip install -r requirements.txt` inside container.
   - Verify `from pgvector.sqlalchemy import Vector` imports.

2. **Enable pgvector**
   - Add `CREATE EXTENSION IF NOT EXISTS vector;` to alembic 0010 first op.
   - Test on local PG16 container.

3. **Create SQLAlchemy models** (each file ≤80 LOC)
   - `kb_document.py` — `KbDocument(TimestampMixin, Base)` with source_type, source_ref unique constraint.
   - `kb_chunk.py` — `KbChunk(Base)` with `embedding: Mapped[list[float]] = mapped_column(Vector(768))`.
   - `conversation.py` — `ChatConversation` with user_id FK, nullable pdf_context_id.
   - `message.py` — `ChatMessage` with conversation_id FK, citations as JSON.
   - `quota_usage.py` — `ChatQuotaUsage` composite PK (user_id, date).

4. **Alembic migration 0010**
   - `op.execute("CREATE EXTENSION IF NOT EXISTS vector")`.
   - Create all 5 tables + indexes (HNSW on kb_chunks.embedding).
   - Downgrade: drop tables in reverse + `DROP EXTENSION vector` if no other usage.

5. **Embedding service**
   ```python
   # app/services/chat/embedding_service.py (≤120 LOC)
   class EmbeddingService:
       async def embed_one(self, text: str) -> list[float]: ...
       async def embed_batch(self, texts: list[str]) -> list[list[float]]: ...
       # Retry: 3 attempts, exponential backoff (1s, 2s, 4s)
       # Batch size: 100 texts per request
   ```

6. **Chunker** (`chunker.py`, ≤80 LOC)
   - Use `tiktoken.encoding_for_model("cl100k_base")` (close enough to Gemini for sizing).
   - Split by paragraph first, then enforce 500 token max per chunk, 50 overlap.
   - Preserve sentence boundaries.

7. **KB ingestion service**
   ```python
   # app/services/chat/kb_ingestion_service.py (≤180 LOC)
   class KbIngestionService:
       async def upsert_document(self, source_type, source_ref, title, content, metadata) -> KbDocument
       async def reindex_document(self, document_id)  # delete old chunks + re-chunk + re-embed
       async def delete_document(self, source_type, source_ref)
   ```
   - On upsert: chunk → embed batch → DELETE old chunks for doc → INSERT new chunks.
   - Transactional (rollback on embed failure).

8. **KB sync event listeners**
   ```python
   # app/services/chat/kb_sync.py (≤100 LOC)
   def register_kb_sync_listeners(numerology_models: list[type]):
       for model in numerology_models:
           event.listen(model, "after_insert", _on_save)
           event.listen(model, "after_update", _on_save)
           event.listen(model, "after_delete", _on_delete)
   ```
   - `_on_save`: enqueue background task `kb_ingestion_service.upsert_document(...)`.
   - Use FastAPI BackgroundTasks (or APScheduler if already in project) to avoid blocking writes.

9. **Backfill script**
   - `scripts/backfill_kb.py`: iterate 22 numerology content tables, call `upsert_document` for each row.
   - Print progress every 50 rows.
   - Idempotent (UNIQUE constraint on source_type+source_ref).

10. **Wire startup**
    - In `app/main.py` `@app.on_event("startup")`: import numerology content models, call `register_kb_sync_listeners(...)`.

11. **Unit tests**
    - `test_embedding_service.py` — mock Gemini API, assert retry behavior.
    - `test_chunker.py` — chunk known text, assert chunk count + overlap + token counts.
    - `test_kb_ingestion_service.py` — integration test: upsert → re-upsert (update) → verify old chunks deleted.

12. **Run backfill on staging**
    - `python scripts/backfill_kb.py --dry-run` first → verify count.
    - Then `python scripts/backfill_kb.py` for real.
    - Verify with `SELECT COUNT(*) FROM kb_chunks;` ~600-1000 chunks expected.

## Todo List

- [x] Add dependencies to requirements.txt (google-genai, pgvector, tiktoken)
- [x] Install pgvector extension on local dev PG16 (DB image switched to `pgvector/pgvector:pg16`; pgvector 0.8.2 active)
- [x] Create `app/db/models/chat/` package + 5 model files
- [x] Update `app/db/models/__init__.py` exports
- [x] Add Gemini config to `app/config.py` + `.env.example`
- [x] Write alembic migration `0010_chatbot_foundation.py` with pgvector extension + 5 tables + HNSW index
- [x] Test migration on local DB (alembic 0010 applied; 5 tables + HNSW cosine index verified)
- [x] Implement `app/services/chat/embedding_service.py` with retry + batching
- [x] Implement `app/services/chat/chunker.py` with token-aware splitting
- [x] Implement `app/services/chat/kb_ingestion_service.py` (upsert/reindex/delete)
- [x] Implement `app/services/chat/kb_sync.py` event listeners
- [x] Register listeners in `app/main.py` startup
- [x] Write `scripts/backfill_kb.py`
- [x] Write unit tests for embedding, chunker, ingestion (17 tests, all pass)
- [ ] Run backfill on local DB, verify chunk counts (deferred — needs Gemini key + migration applied)
- [x] Compile check: `python -m compileall app/`
- [x] Run test suite: `pytest tests/services/chat/` — 17/17 pass
- [x] Update `docs/system-architecture.md` with KB section (done by docs-manager 2026-05-26)
- [x] Document Gemini API key setup in `docs/deployment-guide.md` (done by docs-manager 2026-05-26)

## Success Criteria
- Alembic 0010 migration applies cleanly on fresh DB.
- pgvector extension active: `SELECT * FROM pg_extension WHERE extname='vector';` returns row.
- Backfill produces >500 chunks across 22 source tables, no duplicates.
- Embedding service unit tests pass with mocked Gemini.
- Editing a numerology content row triggers re-embedding within 5s (visible in logs).
- All new code files ≤200 LOC.

## Risk Assessment

| Risk | Mitigation |
|------|------------|
| pgvector extension not available on prod | Verify with DBA before phase start; have CloudSQL/RDS alternative ready |
| Gemini API rate limit during backfill | Batch size 100, sleep 1s between batches, run off-hours |
| Event listener slows down content CRUD | Use BackgroundTasks (async) — never block request thread |
| Chunk token count drift between tiktoken and Gemini | Test with sample, allow 10% margin in chunk size |
| Re-embedding cascade on bulk updates | Add debounce or skip-flag for bulk operations |

## Security Considerations
- `GEMINI_API_KEY` from env only, never logged.
- Embedding cache layer in P6 to reduce API calls.
- `kb_documents.created_by` references admin user — audit trail.
- No PII in KB content (only numerology generic text).

## Post-Review Fixes Applied (2026-05-26)

After code review (code-review-260526-2058-phase-01-foundation.md), three critical issues (C1/C2/C3) and six non-critical (H10+) were addressed:

**C1 — kb_sync.py race condition fix:**
- Refactored to use session-level `after_commit` + `after_rollback` instead of mapper-level `after_insert/update/delete`.
- Eliminates phantom-doc phantom race: enqueued jobs now only fire after DB transaction confirms.
- Made `register_kb_sync_listeners` idempotent (won't double-register on `--reload`).
- Added `shutdown_kb_sync()` called by lifespan finalizer to cancel pending worker + drain queue on shutdown.

**C2 — embedding_service._is_retryable fix:**
- Switched from loose substring match (`_RETRYABLE_SUBSTRINGS`) to typed exception check on `google.api_core.exceptions` (ServiceUnavailable, DeadlineExceeded, InternalServerError, ResourceExhausted).
- Fallback to bounded token-based list for edge cases; eliminates false-positive retries from user-content errors.

**C3 — metadata type consistency fix:**
- `kb_documents.metadata`, `kb_chunks.metadata`, `chat_messages.citations` all switched to PostgreSQL `JSONB` type (from mixed JSON/JSONB).
- Alembic 0010 updated; ORM models updated.
- `chat_messages.created_at` marked `nullable=False` (aligns with TimestampMixin pattern).

**Deferred (non-critical, Phase 02+):**
- H2: SAVEPOINT wrap in `_replace_chunks` (accept current embed-before-delete order, document risk).
- H4/H5: Promote `_to_source` helper + extract `KB_INGESTABLE_MODELS` constant.
- H6: Already fixed in C1 (idempotency guard added).
- H9: `KbChunk.metadata` unused; will either drop or populate in Phase 02 based on use case.
- H13: Hoist `EmbeddingService` to module singleton.
- Security: Add `max_input_chars` ingestion guard.

All 17 chat unit tests still pass post-fixes.

## Next Steps / Dependencies
- **Unlocks:** Phase 02 (Core Chat) needs `embedding_service`, `kb_chunks`, `chat_conversations`, `chat_messages` tables.
- **Required before:** Phase 03 (User PDF) needs `embedding_service` + `chunker`.
- **Parallel-safe with:** none in this phase (foundation must complete first).
- **Phase 02 blockers:** None; all Phase 01 code-complete and ready for integration.
