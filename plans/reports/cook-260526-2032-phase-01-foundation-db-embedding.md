# Phase 01 — Foundation: DB + Embedding + KB Ingestion — Cook Report

**Date:** 2026-05-26 20:32 (Asia/Bangkok)
**Plan:** `plans/260526-1854-chatbot-rag-pdf-analysis/phase-01-foundation-db-embedding.md`
**Mode:** `/cook` interactive (single-shot completion — no review gates triggered, code-only phase)

## Summary
Implemented foundation layer for chatbot RAG: 5 new ORM models, alembic 0010 with pgvector + HNSW, embedding/chunker/ingestion/sync services, backfill script, 17 unit tests (all pass).

## Files Created
### Models (`app/db/models/chat/`)
- `__init__.py` — package exports
- `kb_document.py` — KbDocument (source_type+source_ref unique)
- `kb_chunk.py` — KbChunk (Vector(768))
- `conversation.py` — ChatConversation
- `message.py` — ChatMessage
- `quota_usage.py` — ChatQuotaUsage (composite PK)

### Services (`app/services/chat/`)
- `__init__.py`
- `embedding_service.py` — Gemini text-embedding-004, batched, retry 3× exp backoff
- `chunker.py` — tiktoken cl100k_base, paragraph→sentence fallback, configurable overlap
- `kb_ingestion_service.py` — upsert/reindex/delete with atomic chunk replacement
- `kb_sync.py` — SQLAlchemy after_insert/update/delete listeners + asyncio worker queue

### Migration / Scripts
- `alembic/versions/0010_chatbot_foundation.py` — pgvector ext + 5 tables + HNSW cosine index
- `scripts/backfill_kb.py` — `--dry-run` supported; reuses `_to_source` from `kb_sync`

### Tests (`tests/services/chat/`)
- `test_chunker.py` — 6 tests
- `test_embedding_service.py` — 6 tests (genai mocked)
- `test_kb_ingestion_service.py` — 5 tests (sqlite in-memory)

## Files Modified
- `pyproject.toml` — added `google-genai>=0.3`, `pgvector>=0.3`, `tiktoken>=0.7`
- `app/config.py` — Gemini config block (api_key, models, batch/chunk sizes)
- `.env.example` — Gemini section
- `app/db/models/__init__.py` — register chat package
- `app/main.py` — wire `register_kb_sync_listeners` in lifespan (gated on `gemini_api_key`)

## Verification
- `python -m compileall app/` → clean (all files compile, py3.12)
- `pytest tests/services/chat/` → **17/17 pass** (chunker 6, embedding 6, ingestion 5)
- Full suite: 193 pass / 14 fail — all 14 failures **pre-existing** (KeyError on admin response shape, 422 vs 403 on `/api/so-hoc`); none touch chat code paths.

## Bug fixed during testing
`Chunker.__init__` used `or` for default fallback → `overlap_tokens=0` silently fell through to settings default (50). Switched to `is None` check. Failing test now passes.

## Deferred (needs runtime environment)
1. **Apply migration 0010** on PG16 dev — `docker compose exec api alembic upgrade head`. pgvector extension installed by migration.
2. **Backfill run** — needs valid `GEMINI_API_KEY`; `python -m scripts.backfill_kb --dry-run` first.
3. **Docs sync** — `docs/system-architecture.md` + `docs/deployment-guide.md` (handoff to docs-manager subagent).

## LOC Compliance (≤200 per file)
| File | LOC |
|------|-----|
| kb_ingestion_service.py | 119 |
| embedding_service.py | 104 |
| chunker.py | 103 |
| kb_sync.py | 99 |
| 0010_chatbot_foundation.py | 138 |
| All others | <80 |

## Open Questions
1. **Vector storage on sqlite tests** — pgvector's bind processor serializes list→string which sqlite accepts. Tests pass, but cosine similarity queries cannot be exercised at unit level → covered in Phase 02 integration tests against PG.
2. **MainNumber multi-content fields** — `kb_sync._to_source` concatenates `content` + `content_2..5` with `\n\n`. Confirm with stakeholder whether each should be a separate KbDocument (one per Roman numeral period) vs. one merged document per code.
3. **PhoneMasterDataModel skipped from ingestion** — schema lacks title/content. Confirm not needed in KB.
4. **Listener registration on startup** — only fires when `GEMINI_API_KEY` is set, so dev without key boots clean. Confirm this gate is acceptable for staging/prod.
