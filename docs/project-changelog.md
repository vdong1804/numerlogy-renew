# Project Changelog

**Format:** [YYYY-MM-DD] — Feature/Fix/Milestone  
**Latest First**

---

## [2026-06-01] — DeepSeek LLM Migration (Chat Service)

**Scope:** Migrate chat LLM from Gemini (flash/pro) to DeepSeek (`deepseek-chat`) via OpenAI-compatible SDK. Embeddings remain on Gemini `text-embedding-004`. Prompt caching removed (DeepSeek handles server-side cache). Config simplified; env-vars renamed.

### Backend
- **LLM Service:** `app/services/chat/llm_service.py` refactored to use `openai.AsyncOpenAI(base_url=https://api.deepseek.com)` with model `deepseek-chat`. Both flash/pro tiers now map to single model.
- **Public API preserved:** `generate()`, `generate_stream()`, `LlmResponse`, `StreamResult`, `LlmError` signatures unchanged. Removed `cached_content` kwarg.
- **Embeddings unchanged:** `text-embedding-004` (768-dim), same pgvector schema, HNSW index retained.
- **Cost monitor updated:** Added `deepseek-chat` to `MODEL_PRICING` ($0.27/$1.10/M tokens, cached $0.07/M). Removed Gemini flash/pro entries.
- **Prompt cache deleted:** Removed `app/services/chat/prompt_cache_service.py`, `app/db/models/chat/prompt_cache_handle.py`. Alembic migration `a1d6e2c84f31_drop_prompt_cache_handles.py` drops `prompt_cache_handles` table.
- **Callers updated:** `app/routers/chat/messages.py`, `_stream_generator.py`, `app/services/chat/kb_sync.py`, `app/jobs/cleanup_semantic_cache.py` stripped of prompt-cache references.
- **Config changes:**
  - Added: `DEEPSEEK_API_KEY`, `DEEPSEEK_BASE_URL=https://api.deepseek.com`, `DEEPSEEK_CHAT_MODEL=deepseek-chat`
  - Removed: `GEMINI_FLASH_MODEL`, `GEMINI_PRO_MODEL`, `PROMPT_CACHE_HIT_THRESHOLD`, `PROMPT_CACHE_TTL_SECONDS`
  - Kept: `GEMINI_API_KEY`, `EMBEDDING_MODEL` (embeddings)
- **Tests:** `test_llm_service.py` new (10 cases pass). Deleted `test_prompt_cache_service.py`. `test_cleanup_semantic_cache.py` reshaped (only `semantic_cache` in return dict). Prompt-cache assertions stripped.

### Documentation
- **system-architecture.md:** Updated LLM service description, removed Phase 2f prompt-cache section, updated pipeline (8 steps → 6 steps).
- **deployment-guide.md:** Added DeepSeek env-var block, removed Gemini flash/pro lines, simplified "Enable APIs" section.
- **chatbot-cost-monitoring.md:** Updated pricing table (DeepSeek rates), removed cached_tokens formula term, updated budget math.
- **chatbot-runbook.md:** Updated "DeepSeek API down" incident (CN region firewall note).
- **development-roadmap.md:** Marked Phase 06 as superseded; removed prompt-cache references.
- **codebase-summary.md:** Removed `prompt_cache_service.py` from inventory; updated Phase 06 highlights.

### Data Migration
- **Alembic:** Migration `a1d6e2c84f31` (post-06-01) drops `prompt_cache_handles` table (no data loss; cache was ephemeral).
- **Backward compatibility:** Semantic cache, quota, and rate-limit services unchanged. Existing conversations readable; no schema breaks.
- **Firewall:** DeepSeek egress via `api.deepseek.com` (CN region). Verify firewall rules before prod cutover.

### Breaking Changes
- None for end-users or API contracts. Internal only: prompt-cache invalidation no longer needed; LLM request latency may differ.

---

## [2026-05-28] — Chatbot Hardening + Launch Readiness Phase 08 (Unreleased)

**Scope:** Production hardening, cost monitoring + alerts, 5-pattern abuse detection (rate spike, prompt injection, resource exhaustion, jailbreak, toxicity), Turnstile CAPTCHA gate, feature flags with rollout %, A/B test LLM variants, DSAR endpoint (user chat data wipe). 3 new ops docs, 39 new tests.

### Backend
- **Services:** CostMonitorService (per-token cost aggregation, alert triggers on budget threshold), AbuseDetectionService (5 heuristic patterns, continuous detection job), FeatureFlagService (rollout % + per-user override), AbTestService (Gemini Flash vs Pro assignment)
- **New endpoints:** DELETE `/api/profile/chat-data` (DSAR wipe, owner-only), GET `/admin/chatbot/cost-monitor` (trends/alerts), POST/PUT/DELETE `/admin/chatbot/feature-flags` (CRUD)
- **Migration 0015:** cost_monitor_events, abuse_detection_logs, feature_flags, ab_test_assignments tables
- **Hardening gate:** _hardening_gate.py middleware (`run_hardening_gates`) blocks requests before LLM pipeline if abuse detected or feature disabled
- **Jobs:** aggregate_chat_metrics (nightly 04:00 UTC cost summary), detect_chat_abuse (streaming pattern detection)
- **CAPTCHA:** Turnstile on chat start (request token verified server-side, fail-closed)
- **Alembic:** 0015 migration

### Tests
- 39 new tests: cost_monitor (8), abuse_detection (12), feature_flags (6), ab_test (5), dsar (4), hardening_gate (4)
- Full suite: 39 Phase 08 + prior phases all pass

---

## [2026-05-28] — Admin Chatbot Tuning Phase 07 (Unreleased)

**Scope:** Backend complete (admin KB upload, prompt override, conversation browser, analytics, manual addon grants). Frontend partial (dashboard + KB manager only; prompt/conversations/analytics UI deferred to Phase 08).

### Backend
- **New services:** `AdminKbService` (PDF/DOCX/TXT/MD extraction, routes via KbIngestionService with source_type='admin_upload'), `PromptSettingsService` (60s TTL cache, audit trail, resolve_system_prompt helper), `ChatAnalyticsService` (SQL aggregations, no LLM)
- **New router:** `/admin/chatbot/*` (all under admin superuser guard)
- **New endpoints:** POST `/kb/upload`, GET/DELETE `/kb/documents/{id}`, GET/PUT/DELETE `/prompt`, GET `/prompt/history`, GET `/conversations` (filter), GET `/conversations/{id}`, GET `/analytics/overview?days=N`, POST `/users/{user_id}/grant-addon`
- **New models:** `chat_system_settings`, `chat_system_settings_history` (Migration 0014)
- **Hybrid prompt design:** In-code SYSTEM_PROMPT default + admin override via chat_system_settings; resolve_system_prompt centralises fallback rule
- **Dependencies:** python-docx>=1.1 added to pyproject.toml

### Frontend
- **Pages:** `/admin/chatbot` (dashboard), `/admin/chatbot/kb` (KB manager)
- **Components:** `kb-upload-form.tsx`, `kb-document-list.tsx`, `chatbot-types.ts`
- **Navigation:** "Chatbot RAG" group added to admin-nav-config.ts
- **Deferred scope:** Prompt editor UI, conversation browser UI, analytics dashboard (Phase 08)

### Test Status
- Backend: All tests pass (count TBD)
- Frontend: TypeScript clean, ESLint clean
- Integration: Phase 07 endpoints manual tested (curl + admin UI)

### Known Limitations
- **Frontend UI incomplete:** Prompt override editor, conversation/analytics views deferred (functional backend endpoints ready)
- **Admin runbook deferred:** Task planning doc noted for Phase 08+ (how-to KB upload, prompt tuning, addon granting)

---

## [2026-05-28] — Semantic Cache + Prompt Cache + Rate Limit Phase 06 (Unreleased)

**Scope:** Optimize cost (semantic cache + Gemini prompt caching) and prevent abuse (two-bucket rate limiting) with fail-closed policy. 345 tests pass, 0 failed.

### Backend
- **New services:** `SemanticCacheService` (pgvector cosine lookup, tier-scoped, 24h TTL, NO_INFO exclusion), `RateLimitService` (two-bucket atomic, user+IP, fail-closed, Asia/Bangkok TZ), `PromptCacheService` (SHA256 cache_key, lazy threshold 5 hits, TTL 1h refresh)
- **New routers:** None (pipeline integrated into existing `/api/chat/conversations/{id}/messages` and `...messages/stream`)
- **New models:** `SemanticCacheEntry`, `RateLimitBucket`, `PromptCacheHandle` tables
- **Migration 0013:** 3 new tables + HNSW index (requires pgvector ≥0.5.0)
- **Modified:** `messages.py` (pipeline: rate limit → quota → retrieval → semantic cache → prompt cache → LLM → cache insert), `_stream_generator.py` (stream variant), `llm_service.py` (cached_content kwarg, google-genai 1.47.0)
- **New job:** `cleanup_semantic_cache.run()` at cron(hour=3, minute=15) UTC
- **Config:** No new env vars (all settings-backed: threshold=0.92, ttl_hours=24, hit_threshold=5, ttl_seconds=3600)

### Frontend
- **New hook:** `use-rate-limit-countdown.ts` (countdown display on message input)
- **Modified:** `MessageInput.tsx` (send button disable during lockout), `use-chat-stream` (HTTP 429 handler, Retry-After parsing)
- **Toasts:** Sonner variants: bucket_empty (warn, 3s), daily_cap (error, 8s)

### Code Review Fixes Applied (3 critical + selected high)
- **C1 — Prompt-cache invalidation gated by content hash:** `_replace_chunks` in `kb_ingestion_service.py` short-circuits when chunk SHA-256 unchanged; no-op KB re-syncs no longer wipe prompt cache
- **C2 — Daily cap retry-after uses Asia/Bangkok midnight:** `rate_limit_service.py` `_seconds_to_next_bangkok_midnight` helper + daily counter reset uses Bangkok local date
- **C3 — Rate-limit row lock released before LLM call:** `_transact` commits its own transaction on all paths; outer request reads a fresh transaction
- **H1 — Fail-closed policy:** `OperationalError`/`SQLAlchemyError`/unknown exceptions return `allowed=False, reason="service_error", retry_after=5.0` (was fail-open)
- **H6 — Pipeline reordered:** rate limit BEFORE quota; new `QuotaService.peek_tier()` provides cheap tier lookup pre-rate-limit
- **H7 — Stream cache-hit chunked:** `_stream_cached_answer` yields ~40-char deltas with 20ms delay for streaming UX feel
- **H8 (FE) — `useRateLimitCountdown` interval cleanup** fixed (redundant tick removed)
- **C6 (FE) — Dead SSE `rate_limited` branch removed** from `use-chat-stream` (backend confirmed: 429 always HTTP, never SSE)
- **M4 — `NO_INFO_VI` responses skip cache insert** (prevents stuck no-info on stale KB)
- **M5 — Cache insert in own try/commit/rollback** after assistant message commit (decoupled from assistant-message transaction)

### Known Limitations / Follow-ups
- **H2** cleanup job single-txn for both deletes — all-or-nothing rollback (low risk)
- **H3** `_ensure_bucket` writes on every hot-path request (perf optimization, profile at scale)
- **H4** `_HitCounter` race causes orphan Gemini caches at multi-worker scale
- **H5** NUMERIC(10,2) coupling brittle
- File LOC > 200: `prompt_cache_service.py` 330, `messages.py` 233 (split when next touched)
- Per-chunk reverse index for `invalidate_for_chunks` (Phase 08)
- Load test 100 RPS + monitor cache hit rate 24h on staging
- Tune similarity threshold 0.92 with production false-positive samples
- pgvector ≥ 0.5.0 required for HNSW index (documented in deployment-guide)

### Reports
See: `plans/reports/` Phase 06 step reports + code review at `code-review-260528-1115-phase-06.md`

---

## [2026-05-28] — Chat Quota + Add-on Packages Phase 05 (Unreleased)

**Scope:** Monetize chat with per-message quotas (free 3/day) + purchasable message pack add-ons (Flash/Pro tiers, 30d validity). SePay webhook integration for auto-fulfillment.

### Backend
- **New services:** `QuotaService` (check/decrement with atomic SELECT FOR UPDATE on addon, ON CONFLICT on free), `addon_fulfillment.fulfill_chat_addon()` (idempotent via payment_id uniqueness)
- **New routers:** `/api/chat/addons` (GET list, POST purchase), `/api/chat/quota` (GET user quota)
- **New models:** `ChatAddonPurchase`, `AddonPackageOut`, `QuotaOut`, `QuotaDecision`, `QuotaConflictError`
- **Migration 0012:** adds `chat_addon_purchases` table + `packages(package_kind, message_count, tier, validity_days)` columns
- **Modified:** `messages.py` (quota gate + sync decrement), `_stream_generator.py` (quota decrement pre-commit), `payment_service.py` (branched approval on package_kind)
- **SePay webhook:** Extended matcher to handle `CHATADDON<id>` content prefix (alongside NSQ ref codes)
- **Tests:** 290 total pass, 0 failed; tsc + lint clean

### Frontend
- **New components:** `QuotaBadge` (display remaining quota + tier), `UpsellModal` (bank info + polling), AddonList/AddonCard (in /chat/upgrade page)
- **New hooks:** `use-quota` (polling, 10s default, 5min cap)
- **Modified:** `ChatLayout` (quota display + upsell trigger), `use-chat-stream` (onQuotaExceeded callback + 402/SSE quota_exceeded handling)
- **Admin:** package form gained `package_kind` selector + conditional ChatAddonFields with zod validation

### Code Review Fixes Applied (4 critical + selected high)
- **C1 — SePay webhook fulfills chat addons:** matcher now parses `CHATADDON{payment_id}` content → `approve_payment` (idempotent)
- **C2 — Stream decrement before commit:** single-transaction with assistant message; closes disconnect revenue leak
- **C3 — Backend Pydantic model_validator:** rejects chat_addon with missing/invalid message_count, tier, validity_days
- **C4 — Removed `.prettierrc.json`** (conflicted with team config)
- **H1+H4 — SSE `quota_exceeded_postcommit`** emitted on rare check/decrement race
- **H2 — `onQuotaExceededRef` + `useCallback`** stabilizes callback identity
- **H3 — Quota polling (10s, 5min cap)** with sonner toast on `/chat/upgrade` + UpsellModal
- **H5 — `PackageOut.field_validator`** coerces NULL `package_kind`

### Known Limitations / Follow-ups
- **H1 reserve-then-release** — not implemented; rare race can over-grant by 1 (mitigated by SSE notification)
- **H6 — UTC date reset** at 07:00 Asia/Bangkok local — UI tooltip recommended (Phase 07)
- **H7 — tier Literal case-sensitivity** — no active bug; admin form enforces lowercase
- **Seed addon packages** on staging — manual admin task (Basic/Standard/Premium)
- **Manual E2E**: exhaust free → upsell → bank transfer → webhook fulfill → confirm Pro answers

### Reports
See: Phase 05 Step 1-3 reports + code review at `plans/reports/`

---

## [2026-05-27] — Streaming Chat UI & Backend Phase 04 (Unreleased)

**Scope:** Server-Sent Events (SSE) streaming endpoint, full Next.js /chat UI with conversation sidebar, message thread, citation drawer, PDF upload.

### Added — Backend Streaming

**New Modules:**
- `app/services/chat/sse_formatter.py` (33 LOC): `sse_event(event, data) -> bytes` helper
- `app/services/chat/chat_turn.py` (97 LOC): Extracted shared logic (persist_user_message, run_retrieval, build_turn_prompt, persist_assistant_message) — used by both sync + stream endpoints
- `app/routers/chat/_stream_generator.py` (120 LOC): Async generator for SSE event emission; bridges sync LLM iterator to async via threading + queue

**Modified:**
- `app/services/chat/llm_service.py`: +83 LOC (StreamResult dataclass, generate_stream async method, bridge pattern for sync→async conversion)
- `app/routers/chat/messages.py`: Rewritten (185 LOC, ≤220 target met); delegates to chat_turn helpers, adds POST .../messages/stream endpoint

**Endpoint:**
- POST `/api/chat/conversations/{id}/messages/stream` — SSE streaming response (HTTP/1.1 keepalive required)
- Accepts `MessageIn(content, pdf_context_id?)` (pdf_context_id optional override)

**SSE Events:**
- `delta`: Token-by-token LLM output
- `citations`: Final citation list with metadata
- `done`: Completion + token counts + model used
- `error`: LLM or retrieval failure (code: llm_error/internal_error)

**Behavior:**
- Ownership check + user message persist **before** generator starts (404/422 normal HTTP responses)
- Retrieval failure: emit delta with "Tôi không có đủ thông tin..." phrase; persist canonical row; emit done (LLM not called)
- Mid-stream LLM error: emit error event; no broken assistant row persisted

**Testing:** 40 backend tests pass (13 new stream tests: happy-path 7, retrieval-fail 1, llm-error 2, ownership/auth 3)

---

## [2026-05-27] — Streaming Chat UI Frontend Phase 04 (Unreleased)

**Scope:** Complete Next.js /chat page + ChatLayout + 13 component/hook files for conversation management, message streaming, citation browsing, PDF upload.

### Added — Frontend Chat Module

**New Page:**
- `src/pages/chat.tsx` (52 LOC): Auth guard (→ /login if unauth), renders ChatLayout inside Main

**New Module (src/modules/chat/):**
- **api/chat-api.ts** (100 LOC): Axios wrappers (listConversations, createConversation, deleteConversation, listMessages, uploadPdf, clearPdfContext)
- **hooks/use-conversations.ts** (62 LOC): List/create/delete with useState (TODO: migrate to React Query when available)
- **hooks/use-messages.ts** (48 LOC): Fetch + append for active conversation
- **hooks/use-chat-stream.ts** (228 LOC): SSE consumer via while-loop pump, token batching via rAF, stale-closure-safe fullTextRef
- **hooks/use-pdf-upload.ts** (58 LOC): Multipart PDF upload, 20MB client-side cap, type guard
- **parts/MessageMarkdown.tsx** (88 LOC): react-markdown + remark-gfm + rehype-sanitize; [N] tokens → clickable citations
- **parts/CitationDrawer.tsx** (78 LOC): Right-slide Sheet showing index, title, source type, score bar
- **parts/PdfUploadButton.tsx** (82 LOC): File picker + attached-pill + remove button
- **parts/ConversationSidebar.tsx** (96 LOC): Conversation list + "Cuộc trò chuyện mới" + per-item delete with confirm
- **parts/MessageInput.tsx** (118 LOC): Auto-expanding textarea ≤8 rows, Enter/Shift+Enter, send/cancel/PDF buttons
- **parts/MessageThread.tsx** (204 LOC): History + streaming bubble + skeleton + auto-scroll with isNearBottom guard
- **ChatLayout.tsx** (204 LOC): 3-column desktop (260px sidebar | 1fr thread | right drawer), mobile → Sheet

**npm Packages Added:**
- `react-markdown@^9.x`, `remark-gfm@^4.x`, `rehype-sanitize@^6.x`

**Modified:**
- `src/layouts/Header.tsx`: Added "Chat AI" button (desktop) + MenuItem (mobile), visible if `user !== null`

**Testing:**
- TypeScript: zero errors (new chat files)
- ESLint: zero lint errors (chat scope)
- Build: clean (57.8 kB /chat page)

**Known Gaps:**
- use-conversations.ts TODO: migrate to React Query (not in project yet)
- use-messages.ts TODO: infinite scroll / cursor pagination (loads first page only)
- MessageThread TODO: react-window virtualization (for >100 messages)
- Mobile breakpoint QA: 360px, 768px, 1280px (marked for manual test)
- Citation drawer: chunk content text not included (backend citations event lacks chunk_text)

---

## [2026-05-26] — Chatbot RAG Foundation Phase 01 (Unreleased)

**Scope:** Knowledge base + embedding infrastructure for future RAG chatbot (admin-only feature, no user-facing endpoints yet).

### Added — Data Models
- **5 new tables:** kb_documents (source_type+source_ref natural key), kb_chunks (768-dim embedding), chat_conversations, chat_messages, chat_quota_usage
- **Migration 0010:** pgvector extension auto-install, HNSW cosine index on kb_chunks.embedding, JSONB metadata columns
- **ORM models:** `app/db/models/chat/` (kb_document.py, kb_chunk.py, conversation.py, message.py, quota_usage.py)

### Added — Services & Ingestion
- **EmbeddingService:** Gemini text-embedding-004, batch processing (100 texts/call), 3× retry exp backoff
- **Chunker:** tiktoken-based (cl100k_base), 500-token windows + 50-token overlap, paragraph→sentence fallback
- **KbIngestionService:** atomic document upsert/reindex/delete, manages chunk lifecycle within transactions
- **kb_sync module:** SQLAlchemy after_insert/update/delete listeners + asyncio worker queue, lifespan registration (gated on GEMINI_API_KEY)

### Added — Utilities
- **backfill_kb.py:** one-shot script to ingest numerology content (--dry-run mode supported), idempotent re-run safe
- **Config vars:** GEMINI_API_KEY, EMBEDDING_MODEL, GEMINI_FLASH_MODEL, GEMINI_PRO_MODEL, EMBEDDING_BATCH_SIZE, CHUNK_MAX_TOKENS, CHUNK_OVERLAP_TOKENS

### Added — Testing
- **17 unit tests:** chunker (6), embedding_service (6 + genai mocked), kb_ingestion_service (5 + sqlite in-memory)
- **All tests pass:** 17/17 green, full suite 193/207 pass (14 pre-existing failures unrelated to chat code)

### Dependencies
- `google-genai>=0.3`, `pgvector>=0.3`, `tiktoken>=0.7` added to pyproject.toml

### Post-Review Fixes Applied
- **C1 — Race condition:** Switched kb_sync listeners from mapper `after_insert/update/delete` (fires during flush) to session-level `after_commit` / `after_rollback`. Phantom-doc race on rollback now impossible. `register_kb_sync_listeners` made idempotent (tracks already-attached models). Added `shutdown_kb_sync()` lifespan hook for clean queue drain.
- **C2 — Retry typing:** `embedding_service._is_retryable` now inspects typed `exc.code` / `exc.status_code` (HTTP status codes 408/429/500/502/503/504) before falling back to a bounded token list ("deadline exceeded", "service unavailable", "resource exhausted", etc). No more loose substring matches on "internal" or "500".
- **C3 — JSONB unification:** `kb_documents.metadata`, `kb_chunks.metadata`, `chat_messages.citations` all switched to PostgreSQL `JSONB` with `with_variant(JSON(), "sqlite")` fallback for unit tests. `chat_messages.created_at` set to `nullable=False`.
- All 17 chat unit tests still pass after these fixes.

### Known Limitations (Phase 01)
- **Vector queries on SQLite:** Unit tests use pgvector bind processor; cosine similarity queries untestable without real Postgres. Covered by deferred Phase 02 integration tests.
- **Cosine similarity coverage:** Real-PG integration test deferred to Phase 02.
- **Listener registered only when `GEMINI_API_KEY` is set** — staging/prod must set the key for KB auto-sync to engage.

### Breaking Changes
- None (new feature only; no existing code affected)

### Docs Updated
- `docs/system-architecture.md` — added "Knowledge Base & Chat" subsection (tables, services, sync flow)
- `docs/deployment-guide.md` — added "Gemini API Setup" section (API key creation, backfill instructions)
- `docs/development-roadmap.md` — Chatbot RAG phases planned

### Next Steps (Phase 02+)
1. Integration tests vs real Postgres (cosine similarity queries)
2. RAG retrieval endpoint + LLM generation (Gemini 2.0 Flash)
3. Promote `_to_source` to public helper module (DRY w/ backfill script)
4. Add `max_input_chars` guard for ingestion DoS protection

---

## [2026-05-27] — User PDF Context Phase 03 (Unreleased)

**Scope:** User-uploaded PDF attachment to conversations, hybrid KB + PDF retrieval (PDF-favored split), 30-day TTL with nightly cleanup.

### Added — Data Models
- **2 new tables:** user_pdf_index (user_id, pdf_hash SHA-256, filename, page_count, expires_at 30d TTL, UNIQUE(user_id, pdf_hash)), user_pdf_chunks (pdf_index_id FK, page_number, content, embedding Vector(768), HNSW index)
- **Migration 0011:** user_pdf_index + user_pdf_chunks creation, chat_conversations.pdf_context_id FK (SET NULL on cascade)
- **ORM models:** UserPdfIndex, UserPdfChunk (app/db/models/chat/)
- **user_reports modification:** file_hash column added (for backfill script)

### Added — Services & Upload
- **PdfMatchService:** SHA-256 hash file, user-scoped lookup of existing PDFs
- **PdfParserService:** pypdf extract_pages + clean_text (normalize whitespace, hyphen repair)
- **UserPdfService:** Orchestrate match-or-parse, atomic insert with IntegrityError recovery (race-condition safe), TTL slide on re-upload
- **3 new endpoints:**
  - POST `/api/chat/conversations/{id}/upload-pdf` — multipart form, 25MB cap, %PDF magic-bytes, auto-attach (201)
  - PATCH `/api/chat/conversations/{id}/pdf-context` — attach/clear pdf_context_id (ownership validated, 200)
  - DELETE `/api/chat/conversations/{id}/pdf-context` — clear attachment (204)

### Added — Hybrid Retrieval
- **Retrieval merge:** When pdf_context_id given, split top_k (PDF-favored: 2 PDF + 1 KB on free tier top_k=3), merge by score, dedup
- **KB-only path:** Preserved when no PDF attached (zero Phase 02 compat overhead)
- **PDF citations:** JOIN user_pdf_index.filename → title; citation reads "report.pdf/p4" not "user_pdf/4"
- **Streaming size check:** 1MB chunk reads, 413 abort at 25MB (no full-body buffer)

### Added — Cleanup & TTL
- **30-day TTL:** expires_at auto-set on insert; nightly cleanup 03:00 UTC deletes expired rows + cascades chunks
- **TTL slide:** Re-upload refreshes expires_at (active PDFs don't die at day 30 boundary)
- **Temp sweep:** Cleanup also removes /media/chat_uploads files >1h old

### Added — Configuration
- USER_PDF_TTL_DAYS=30, USER_PDF_MAX_BYTES=26214400 (25MB), PDF_CHUNK_TOKEN_WINDOW=500, PDF_CHUNK_OVERLAP_TOKENS=50
- nginx: client_max_body_size 26M (headroom above app cap)

### Added — Backfill Script
- `scripts/backfill_pdf_hashes.py` — one-shot SHA-256 over user_reports.pdf_path (idempotent, skips missing files)

### Added — Testing
- **82 chat tests pass** (full suite 257/271, +17 new PDF tests: pdf_match, pdf_parser, user_pdf_service, pdf_upload, retrieval_merge)
- All Phase 03 new code: 27 tests + Phase 01/02 tests

### Post-Review Fixes Applied (2026-05-27)
**All 5 high/should-fix items from code review marked APPLIED (not deferred):**
- **F1 — Streaming size check:** Implemented 1MB chunk-based read with running size check; 413 fires before full buffer. Nginx cap raised to 26M for app ownership of contract.
- **F2 — KB/PDF split documented:** Split is PDF-favored intentionally (user's doc is the intent); marked in code. Over-budget bug fixed: when kb_k==0, skip KB query entirely.
- **F3 — Atomic insert race:** IntegrityError on (user_id, pdf_hash) UNIQUE now caught; re-query winner + TTL slide. User gets success response, not 500.
- **F5 — TTL slide on re-upload:** Re-uploading same PDF bumps expires_at to now() + 30d (actively-used PDFs don't die at exactly day 30).
- **F6 — PDF citation filenames:** PDF rows JOIN user_pdf_index.filename → frontend reads "report.pdf/p4" not opaque "user_pdf/4".

### Known Limitations (Phase 03)
- **Cleanup-job race window:** Expired PDF may be deleted between SELECT and user's re-upload insert (edge case, rare; new insert gets fresh expires_at so survives)
- **Hash trust on disk:** If user_reports.pdf_path file is regenerated without updating file_hash, parser uses stale bytes (low likelihood; no write hook enforces invariant)

### Dependencies
- `pypdf>=4.0` added to pyproject.toml

### Docs Updated
- `docs/system-architecture.md` — added "User PDF Context (Phase 03)" subsection (tables, hybrid flow, TTL, endpoints)
- `docs/deployment-guide.md` — added "Phase 03: User PDF Context" (endpoints, nginx config, migration, cleanup, backfill)
- `docs/project-changelog.md` — Phase 03 entry with deliverables + applied fixes
- `docs/development-roadmap.md` — Phase 03 status → Complete, fixes listed

### Next Steps (Phase 04+)
1. Streaming chat endpoint (SSE) with per-message citations
2. User quota tracking per month
3. Rate limiting per tier
4. Real-PG integration tests (PDF attachment → message flow)

---

## [2026-05-26] — Chatbot RAG Core Phase 02 (Unreleased)

**Scope:** Chat endpoints + RAG retrieval + LLM generation + citation extraction. Full conversational interface with anti-hallucination safeguards.

### Added — Chat API Endpoints (5 new)
- **POST /api/chat/conversations** — Create conversation (auth required, 201)
- **GET /api/chat/conversations** — List user's conversations (paginated)
- **GET /api/chat/conversations/{id}** — Conversation detail (404 if not owner)
- **DELETE /api/chat/conversations/{id}** — Delete with cascading message cleanup (204)
- **GET /api/chat/conversations/{id}/messages** — List messages
- **POST /api/chat/conversations/{id}/messages** — Send message → retrieve KB → generate with LLM → return assistant reply + citations (201)

### Added — Retrieval & Generation Services
- **RetrievalService:** pgvector top-k cosine similarity (free tier: 3 chunks, threshold 0.6), similarity threshold enforced
- **LlmService:** Gemini Flash/Pro wrapper, 30s timeout via `asyncio.wait_for`, empty-response guard (raises `LlmError` on safety filter), streaming-ready interface
- **PromptBuilder:** System prompt with anti-hallucination contract ("Tôi không có đủ thông tin để trả lời câu hỏi này." when KB insufficient), user message sanitization, chat history max 5 turns, Gemini prompt caching constant
- **CitationParser:** Regex-based [N] extraction from LLM text, bounds-check against chunk list, dedup + sort by appearance order

### Added — Configuration
- **RAG_TOP_K_FREE=3, RAG_TOP_K_PAID=8** — Chunks per query (free vs paid tiers)
- **RAG_SIM_THRESHOLD=0.6** — Cosine similarity floor (pgvector index bounds)
- **HISTORY_MAX_MESSAGES=5** — Prior turns in prompt context
- **LLM_TIMEOUT_SECONDS=30** — Gemini API call hard stop

### Added — Testing
- **51 unit + integration tests:** Retrieval service (8), prompt builder (10), LLM service (9), citation parser (6), conversation service (7), routers (11)
- **All tests pass:** 51/51 green on Phase 02 new code, full suite 207+ pass (only Phase 01 pre-existing failures carry forward)

### Added — Ownership & Safety
- **Ownership Enforcement:** Routers validate `user_id` ownership for GET/DELETE/POST to {id}; 404 on mismatch (not 403)
- **Concurrency Safety:** User message committed before LLM call (C1 fix) — 502 won't lose user message
- **Anti-Hallucination:** System prompt teaches LLM to respond "Tôi không có đủ thông tin..." when KB insufficient; retrieval failure short-circuits (H8 fix)
- **Empty Response Guard:** LLM returning empty/safety-filtered text raises `LlmError` (H12 fix) instead of persisting blank message

### Post-Review Fixes Applied (2026-05-26)
- **C1 — User message loss on LLM 502:** Fixed by committing user message to DB (with flush + refresh) before initiating LLM call. Fresh session for assistant message insert. User message now persists even if LLM fails.
- **C2 — Timeout leak on sync HTTP calls:** Added `httpx.Timeout` binding to `genai.Client` initialization (sets per-request socket + conn + read timeouts to 30s). Documented that `asyncio.wait_for` doesn't cancel underlying thread; httpx timeout is the real bound.
- **H8 — Retrieval failure wastes LLM call:** Refactored `messages.send_message` to catch retrieval exception, skip LLM entirely, return canonical phrase directly. Saves cost + gives operators clear log signal.
- **H12 — Empty/safety-blocked LLM response persists as blank:** Added guard in `llm_service.py:93`: if `text.strip() == ""`, raise `LlmError("Empty LLM response (likely safety filter)")` instead of returning empty string. Router catches + returns 502 (not 201 with blank content).

### Known Limitations (Phase 02)
- **Long transaction during LLM call (C1 context):** Still acceptable for Phase 02 (low traffic) but will be refactored in Phase 04 (streaming needs independent connection). Documented in code.
- **Thread pool leak on timeout (C2 context):** Mitigated by httpx timeout binding; google-genai background thread may complete slowly but won't accumulate indefinitely at scale. Phase 04 streaming will replace `to_thread` entirely.

### Breaking Changes
- None (new feature only; no existing endpoints affected)

### Docs Updated
- `docs/system-architecture.md` — added "Chat API (Phase 02)" subsection (endpoints, flow, anti-hallucination contract)
- `docs/deployment-guide.md` — added "Chatbot RAG Chat API Setup" section (config vars, test curl, performance monitoring)
- `docs/project-changelog.md` — Phase 02 entry with deliverables + applied fixes
- `docs/development-roadmap.md` — Phase 02 status → Complete, Phase 03 outlined

### Next Steps (Phase 03+)
1. PDF context filtering (pdf_context_id parameter wiring)
2. Streaming chat endpoint (SSE) with per-message citations
3. User quota tracking per month
4. Rate limiting per tier
5. Real-PG integration tests (cosine similarity on live DB)

---

## [2026-05-26] — Launch Readiness Phase 04 (v1.4)

**Scope:** Admin order management (search/filter/export), SEO image optimization, go-live runbooks, final pre-flight validation.

### Added — Admin Operations
- **Order Search & Filter:** `GET /admin/orders` extended with email (ILIKE partial), ref_code, status, date_from, date_to, pagination (page, page_size 1-100)
- **CSV Export:** `GET /admin/orders/export.csv` StreamingResponse (10k row max, 400 error if exceeded) with params matching list endpoint
- **CSV Format:** 9 columns (order_id, ref_code, user_email, product_names, total_vnd, status, paid_at, refunded_at, created_at), UTF-8 BOM prepended, semicolons separate products, formula-injection sanitized (`=+-@\t\r` prefix escaped)
- **Frontend Search UI:** `src/components/admin/order-search-form.tsx` (email, ref_code, status, date range, Xóa lọc reset, Xuất CSV button), rewritten `src/pages/admin/orders/index.tsx` with pagination + empty state
- **DatePicker TZ Contract:** Bangkok TZ (+07:00) enforced: frontend sends `YYYY-MM-DDT00:00:00+07:00` (from) + `YYYY-MM-DDT23:59:59+07:00` (to), backend documented

### Added — SEO/Performance
- **Image Alt Text Fixes:** Fixed missing/vague alt on 3 images (zodiac.png, satellite.png, adalash_banner.png)
- **next/image Migration:** bg-teacher.png (627KB) + adalash_banner.png (317KB) migrated to Next.js Image component with priority flag for LCP
- **Image Audit:** `docs/image-audit.md` created; tracked 10 img tags, 6 deferred (SVG logos, QR, CDN icons, CSS backgrounds), noted 4 CSS bg images (~5.6MB unaddressed without Cloudflare Polish/WebP)

### Added — Deployment & Operations
- **Go-Live Runbook:** `docs/go-live-runbook.md` (5 sections: pre-flight checklist 16 items, deploy steps 12 steps, rollback triggers, rollback procedure, comms plan)
- **Post-Launch Monitoring:** `docs/post-launch-monitoring.md` (daily/weekly checks, alert thresholds, escalation contacts, incident playbook references)

### Modified — Data Model
- **Order.refunded_at:** Mapped in `app/db/models/order.py` (confirmed by migration 0008, previously unmapped)

### Fixed (Post-Review)
- **C1 — NameError:** `http_http_status` typo → `http_status` in orders.py:145, prevents 500 on search error
- **H1 — ILIKE Injection:** Added `app/utils/query.py::escape_like()` (escapes `\`, `%`, `_` before ILIKE), applied in list_orders + export_orders; added `max_length=200` on email/ref_code Query params
- **H2 — CSV Formula Injection:** Added `_safe_csv_cell()` sanitizer (prefixes `'` if value starts with `=+-@\t\r`), applied to all 9 CSV columns
- **H3 — DatePicker Bangkok TZ:** Added `toIsoWithBangkokTz(dateStr, endOfDay)` helper in order-search-form.tsx, documented backend contract for TZ offset
- **H5 — exportOrdersCsv JSON error UX:** Parse JSON response detail on 400+ error, throw readable message to UI setError handler

### Tests
- **Backend:** 173/190 pass (17 pre-existing failures unchanged from Phase 03, 0 regressions introduced by Phase 04)
- **Frontend build:** PASS (94 pages compiled, 0 errors, sitemap generated, /admin/orders bundle 3.85kB page + 198kB first load JS, no regression)
- **Image audit:** 10 total img tags, 3 fixed, 6 deferred, 4 CSS backgrounds noted

### Config
- No new env vars (uses existing NEXT_PUBLIC_API_BASE, backend API_URL)

### Docs
- `docs/go-live-runbook.md` — pre-flight checklist, deploy steps, rollback, comms plan
- `docs/post-launch-monitoring.md` — daily/weekly checks, alert thresholds, escalation, incident playbook
- `docs/image-audit.md` — full audit of img tags, alt text status, migration decisions

### Follow-ups (Post-Launch)
- Ops actions: DNS Resend + GSC, Sentry signup + real DSN, UptimeRobot signup, Cloudflare Turnstile + DNS proxy, blog 5-10 bài via admin News CRUD, mobile QA real device, mail-tester verify, SSL Labs scan, soft launch beta invite, final E2E + ads enable, fill [BRACKETS] placeholders in legal pages/Contact/Footer (DN info, MST, address, phone, Zalo OA), favicon binary assets (favicon.ico, apple-touch-icon.png, og-default.png)
- Code debt: Admin lint cleanup sprint (defer post-launch per lint-cleanup-backlog.md), Redis cache numerology content (>1k req/min), CI/CD GitHub Actions, formal audit log, Playwright E2E, k6 load test, 2FA admin, formal refund state machine, Prometheus + Grafana monitoring

### Plan Status
- **Launch Readiness Checklist:** Code phases 01-04 shipped. All functional code complete. Pending user external actions (DNS, registrar, API signups, blog content, mobile QA, legal placeholders, asset generation).

---

## [2026-05-26] — Launch Readiness Phase 03 (v1.3)

**Scope:** Security (rate limiting, Turnstile CAPTCHA, Nginx headers), email deliverability (plain-text fallbacks, multipart), UX (FAQ, guide pages, empty states, skeletons), configuration cleanup.

### Added — Security
- **Rate Limiting (slowapi):** `app/middleware/rate_limit.py` with key func (CF-Connecting-IP → X-Forwarded-For → fallback), `Limiter(enabled=settings.rate_limit_enabled)` for test bypass
- **Rate Limit Decorators:** `@limiter.limit("5/minute")` on `/auth/login`, `@limiter.limit("3/minute")` on `/auth/register` and `/auth/forgot-password`, `@limiter.limit("100/minute")` on `/webhooks/sepay`
- **Turnstile CAPTCHA Backend:** `app/services/turnstile_service.py` (httpx verify flow, fail-closed on network error, dev skip when empty secret, 5s timeout), startup assertion in `config.py` when `environment=production`
- **Turnstile CAPTCHA Frontend:** `src/components/turnstile-widget.tsx` (async api.js load, explicit widget, prod error guard on missing siteKey, dev fallback with `NODE_ENV` guard), integration in `register.tsx` + `forgot-password.tsx` (captcha_token state, disabled submit until token present)
- **Nginx Security Headers:** Strict-Transport-Security (2yr HSTS), X-Frame-Options (SAMEORIGIN), X-Content-Type-Options (nosniff), Referrer-Policy, Permissions-Policy, Content-Security-Policy (relaxed for GA/Pixel/Turnstile challenges.cloudflare.com + connect-src corrected)
- **Trusted Proxy Config:** `trusted_proxy_mode: Literal["cloudflare","direct"]` in `config.py`, rate-limit key func adapts based on mode

### Added — Email Deliverability
- **Plain-text Fallbacks:** `welcome.txt`, `password-reset.txt`, `quota-low.txt`, `order-expired.txt`, `order-paid.txt`, `order-refund.txt` (6 pairs matching HTML templates)
- **Jinja2 Text Environment:** `_jinja_txt_env` without autoescape, `render_text_template()` service method
- **Multipart Dispatch:** `email_outbox_service._dispatch_multipart()` sends both text + html to SMTP providers
- **Unsubscribe Footer:** `base.html` inheritance with footer link to `/my-account/settings` via `frontend_url` Jinja variable (auto-injected by `_enrich_payload`)

### Added — UX
- **FAQ Page** (`src/pages/faq.tsx`): 15 Q&A, 3 groups (Mua hàng/Thanh toán/Báo cáo), native `<details>` accordion, SSG, accessible without login
- **Hướng dẫn sử dụng** (`src/pages/huong-dan.tsx`): 5-step guide with numbered badges, placeholder images, CTA buttons (Đăng ký + Cửa hàng), SSG
- **Empty State Component** (`src/components/empty-state.tsx`): Generic MUI icon + title + description + CTA, used in orders/reports when empty
- **Skeleton Loaders:** `order-card-skeleton.tsx`, `report-card-skeleton.tsx`, `shop-item-skeleton.tsx` (Tailwind animate-pulse)
- **My Account Empty States:** orders page (ShoppingBagOutlined icon, CTA → /shop), reports page (DescriptionOutlined icon, CTA → /shop)

### Modified — Configuration
- **next.config.js:** Removed old OAuth env vars (NEXTAUTH_*, GOOGLE_CLIENT_*, FACEBOOK_CLIENT_*, TWITTER_CLIENT_*, DJANGO_AUTH_*), added NEXT_PUBLIC_TURNSTILE_SITE_KEY, retained `ignoreBuildErrors` + `ignoreDuringBuilds` with TODO comment pointing to lint-cleanup-backlog.md
- **.env.example:** Added NEXT_PUBLIC_TURNSTILE_SITE_KEY, RATE_LIMIT_ENABLED, TRUSTED_PROXY_MODE, TURNSTILE_SECRET_KEY entries
- **Footer:** Added `/faq` + `/huong-dan` to LEGAL_LINKS navigation

### Fixed (Post-Review)
- CSP `connect-src` corrected: changed `api.nhansinhquan.vn` → `cms.nhansinhquan.vn`, added `challenges.cloudflare.com` + `www.facebook.com` (reviewer catch C1)
- Turnstile fail-open risk: added startup assertion in `config.py` when `ENVIRONMENT=production` (reviewer catch H1)
- Turnstile dev-skip leak: wrapped dev fallback in `process.env.NODE_ENV !== 'production'` guard, prod renders red error on missing siteKey (reviewer catch H2)
- XFF spoofing risk: added `TRUSTED_PROXY_MODE` setting to distinguish Cloudflare vs direct nginx, rate-limit key func prioritizes CF-Connecting-IP in Cloudflare mode (reviewer catch H3)
- `_forgot_password_key` async: converted to `async def`, parses `await request.json()` directly to extract email (fixes timing bug in per-email rate-limit isolation) (reviewer catch H5)

### Tests
- **Backend:** 173/190 pass (17 pre-existing failures in admin content endpoints, unchanged from Phase 02; +3 new auth register tests all pass)
- **Frontend build:** PASS (0 errors, 94 pages including new `/faq` + `/huong-dan` SSG pages)
- **Security Validation:** Rate limit decorators verified, Turnstile fail-closed path confirmed, Nginx CSP syntax valid, email multipart tested
- **Regression scope:** None (all Phase 03 code paths functional, no impact on pre-existing admin test failures)

### Config
- New: `TURNSTILE_SECRET_KEY`, `NEXT_PUBLIC_TURNSTILE_SITE_KEY`, `RATE_LIMIT_ENABLED`, `TRUSTED_PROXY_MODE`
- Updated: `next.config.js` (OAuth cleanup), `.env.example` (new vars), `env.prod.example` (rate limit + Turnstile + proxy mode)

### Docs
- `docs/lint-cleanup-backlog.md` — Deferred TypeScript/Prettier fixes in admin components, removal of ignore flags blocked until Phase 04 admin cleanup sprint

### Follow-ups (Phase 04 + Post-Launch)
- Ops action: Cloudflare Turnstile dashboard signup → obtain site key + secret key
- Ops action: Confirm Cloudflare proxy active in prod (not DNS-only) or set `TRUSTED_PROXY_MODE=direct`
- Phase 04: Dedicated admin lint cleanup sprint (Prettier + import-sort + nested-ternary), remove `ignoreBuildErrors` + `ignoreDuringBuilds` flags
- Pre-launch: Replace placeholder images in /huong-dan with real screenshots, verify mail-tester delivery, run Lighthouse mobile audit
- Post-launch: SSL Labs security scan, fix footer dead links (#), review slowapi v0.1.9+ compatibility with async key_func

---

## [2026-05-26] — Launch Readiness Phase 01+02 (v1.2)

**Scope:** Legal/SEO compliance (4 pages SSG, cookie consent NĐ13 compliant), SePay reconciliation cron + refund flow, Sentry error tracking skeleton, signed download links.

### Added — Legal & SEO
- `terms.tsx`, `privacy.tsx` (NĐ13/2023 DPO contact), `refund-policy.tsx` (7d/PDF-not-rendered), `contact.tsx` — all SSG
- Cookie consent banner (localStorage 365d, fires `nsq_consent_updated` event)
- GA4 + Meta Pixel gated by consent (`analytics.tsx` + `consent-storage.ts`)
- `next-sitemap` config, `robots.txt` (disallow `/admin`, `/my-account`, `/api`, `/check-out`), `manifest.json` (PWA), Organization JSON-LD in `_document.tsx`
- Meta layout extended: dynamic OG image, Twitter card, canonical auto-gen per route, favicon links

### Added — Payment Safety
- Refund workflow: POST `/admin/orders/{id}/refund` (superuser, reason textarea, idempotent)
- `signed_url.py`: HMAC-SHA256 with `typ: report_download` field, 7d expiry, path traversal guard (`os.path.realpath`)
- `order-paid.txt` (new), `order-refund.html|txt` email templates with signed download links (no login required)
- Migration `0008`: `orders.admin_notes`, `orders.refunded_at`, `orders.status` enum +`refunded`

### Added — Payment Reconciliation
- `reconcile_sepay.py` cron: 15min interval, pulls 24h SePay tx history, idempotent via webhook_events dedup, batch-commit per order (atomic fulfillment)
- `sepay_service.list_recent_transactions(hours=24)` — SePay API wrapper

### Added — Observability
- Sentry Next.js init (skeleton): `sentry.client|server|edge.config.ts`, rate 0.1, env-gated (skip if `SENTRY_DSN` empty)
- Sentry FastAPI init: `beforeSend` PII scrubber (email, phone, JWT regex), filter 4xx + `/health*` endpoints
- Sentry config vars: `NEXT_PUBLIC_SENTRY_DSN`, `SENTRY_DSN`, `ENVIRONMENT`, `RECONCILE_WINDOW_HOURS`

### Fixed (Post-Review)
- `NEXT_PUBLIC_SENTRY_DSN` prefix in client config (was reading wrong env var)
- Sentry `beforeSend` PII scrubber (was no-op, now strips email/phone/JWT)
- Path traversal hardening via `os.path.realpath` + symlink resolution
- `datetime.utcnow()` → `datetime.now(timezone.utc)` (deprecated API)
- Reconcile batch-commit moved inside per-order loop (narrow atomicity, prevent rollback cascades)
- Reconcile idempotency broadened: checks `status IN ('matched','received','duplicate')` not just `matched`
- Signed token `typ` field prevents cross-purpose token reuse
- Email payloads: `settings.media_url.replace("/media", "")` → `settings.frontend_url.rstrip("/")` (no fragile string replace)
- Refund endpoint pre-checks order status before API call (idempotency flag set correctly)

### Tests
- 175/190 pass (15 pre-existing failures unchanged, no regression from Phase 01+02 code)
- Signed URL + reconcile cron untested (TODO Phase 03)

### Config
- New: `SENTRY_DSN`, `NEXT_PUBLIC_SENTRY_DSN`, `ENVIRONMENT`, `RECONCILE_WINDOW_HOURS=24`
- Updated: `NEXT_PUBLIC_SITE_URL` (for canonical links), `NEXT_PUBLIC_APP_VERSION` (footer)

### Docs
- `docs/analytics-events.md` — event taxonomy, consent flow, env var reference
- `docs/legal-content-sources.md` — template versions, placeholder index (MST, address, phone, DPO contact, email)
- `docs/runbook-payment-incident.md` — 3 scenarios: missed webhook, refund request, cron failure + troubleshooting

### Follow-ups (Phase 03+04)
- Rate limiting (slowapi), Turnstile, Nginx security headers, FAQ/Hướng dẫn, mobile QA
- Fill legal page placeholders, DNS/SPF/DKIM, GSC sitemap submit, Sentry user signup + real DSN
- Blog content, Cloudflare CDN, go-live runbook
- Signed URL + reconcile unit tests

---

## [2026-05-26] — Account & Transaction Management (v1.1)

**Scope:** Hybrid pricing (quota packages + standalone reports + combos), SePay-automated payments, /my-account self-service, admin orders dashboard, transactional email outbox.

### Added — Data model (migrations 0004–0007)
- `products` + `product_items` (combo composition)
- `orders` + `order_items` (server-priced, `NSQ-XXXXXXXX` ref codes via Crockford base32)
- `user_reports` (generated PDFs, owner-only download path)
- `webhook_events` (SePay audit log + idempotency on `(provider, sepay_tx_id)`)
- `email_outbox` (status / attempts / backoff for transactional mail)
- `user_profiles.notification_prefs` + (Phase 06) `last_quota_warning_at`

### Added — Backend
- `/api/shop/*` public catalogue
- `/api/orders` create + status polling (owner-only)
- `/api/webhooks/sepay` — Apikey auth, IP allowlist, `FOR UPDATE` order lock, ±1k VND tolerance, idempotent re-delivery
- `/api/my/*` — dashboard, orders, reports library, password change, notification prefs
- `/admin/products|orders|dashboard|webhook-events`
- `services/order_service`, `sepay_service`, `fulfillment_service`, `dashboard_service`, `email_outbox_service`
- `utils/ref_code.generate_ref_code()` (28-char alphabet, ambiguous chars stripped)
- Resend + SMTP email providers behind a common `EmailProvider` interface
- Jinja2 email templates: `welcome`, `order-paid`, `order-expired`, `quota-low`, `password-reset`
- Report templates: `base_report`, `report-overview`, `report-love`, `report-career`, `report-mini`
- APScheduler in-process: `email_dispatcher` (1m), `expire_pending_orders` (5m), `cleanup_outbox` (daily 3 AM Bangkok)
- `/health/detail` (DB + provider config status)
- Lead-magnet free report granted via FastAPI `BackgroundTasks` on register

### Added — Frontend
- `/shop` catalogue + `/shop/[slug]` detail with conditional report-input form
- `/check-out/[orderId]` QR placeholder + ref_code copy + 3s status poller + auto-redirect on paid
- `/my-account` (dashboard, orders, reports, profile/password, settings)
- `/admin/products`, `/admin/orders`, `/admin/orders/[id]` (with Mark-as-Paid), `/admin/webhook-events`
- Sidebar nav extended (Sản phẩm, Đơn hàng, Webhook Events)
- `lib/shop-api.ts`, `lib/my-account-api.ts`, `lib/admin-dashboard-api.ts`

### Tests
- `tests/unit/test_ref_code.py` — format + 10k-iteration uniqueness + ambiguous-char exclusion
- `tests/unit/test_sepay_service.py` — `parse_ref_code` parametric + constant-time apikey check
- `tests/unit/test_order_service.py` — server-side total, missing/inactive product rejection

### Config
- `SEPAY_API_KEY`, `SEPAY_AMOUNT_TOLERANCE_VND`, `SEPAY_WEBHOOK_IP_WHITELIST`
- `RESEND_API_KEY`, `RESEND_FROM_EMAIL`
- `BANK_ACCOUNT_NUMBER`, `BANK_ACCOUNT_HOLDER`, `BANK_CODE`, `BANK_NAME`

### Preserved
- Legacy `packages` / `user_payments` / `user_packages` tables and their endpoints (parallel migration; not dropped).

### Follow-ups (Phase 2)
- Refund workflow + formal admin audit log
- Reconcile-SePay cron (pull recent transactions when webhook misses)
- Rate-limiting middleware (slowapi) + Sentry integration
- k6 webhook load test + Cypress E2E flows

---

## [2026-05-25] — User Site Auth Overhaul

**Scope:** Remove SNS login, ship email/password flow on the public landing page.

### Removed
- Google / Facebook / Twitter OAuth on the user site (next-auth + SessionProvider).
- FastAPI OAuth routes (`/auth/google*`, `/auth/facebook*`), `app/core/oauth.py`, `social_accounts` table, related env vars (`GOOGLE_*`, `FACEBOOK_*`, `OAUTH_REDIRECT_BASE`).
- Legacy `convertTokenSocial` helper + Django-era SNS constants on the frontend.

### Added
- `POST /auth/forgot-password` — issues a hashed, single-use reset token; always returns 202 (no email enumeration); invalidates prior outstanding tokens.
- `POST /auth/reset-password` — consumes token, updates password, revokes all refresh tokens; rejects inactive users.
- `password_reset_tokens` table (migration `0003_drop_social_add_reset.py`).
- SMTP helper (`app/services/email_service.py`) with log fallback when `SMTP_HOST` empty.
- Frontend pages: `/login`, `/register`, `/forgot-password`, `/reset-password`.
- `src/lib/user-auth.ts` (js-cookie helpers + `useUserAuth` hook) and `src/lib/user-api.ts` (fetch wrapper).
- Cookie `Secure` flag in production (XSS surface noted as known trade-off vs HttpOnly).

### Fixed
- Refresh token JWT collision on rapid rotation within the same second (added `jti` claim).
- Test infrastructure: SQLite + `BigInteger` autoincrement; test DB override now commits like production.

### Config
- New env keys: `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM`, `SMTP_USE_TLS`, `PASSWORD_RESET_TOKEN_EXPIRE_MINUTES`, `PASSWORD_RESET_URL_PATH`.

### Follow-ups
- Rate-limit `/auth/forgot-password` per IP+email.
- Consider HttpOnly server-set cookies once SSR session route is in place.

---

## [2026-05-25] — Initial FastAPI Release (v1.0)

**Milestone:** Django → FastAPI migration complete. Production-ready deployment.

### Features Shipped
- **Authentication:** JWT + refresh token rotation, Google/Facebook OAuth, superuser role-based admin access
- **Numerology PDF Generation:** Paid quota-gated PDF downloads via `/api/so-hoc` (async wkhtmltopdf), free readings via `/api/so-hoc-free`, horoscope chart via vietheart.net integration
- **Numerology Calculations:** 9 number types (so_chu_dao, so_nam_ca_nhan, etc.) with master number redirects (11→2, 22→4, 33→6), Vietnamese accent handling
- **Content Management:** 22 numerology content tables, editable via admin UI (TipTap rich-text editor with image upload)
- **News & Blog:** Full CRUD for news articles with featured images
- **Package Management:** Free/Basic/Premium tiers, quota assignment, renewal days configuration
- **Payment Tracking:** User payment records (pending/approved/rejected), admin approval workflow with reason tracking
- **User Profiles:** Birthday, gender, address, quota balance, download history audit log
- **Banking Information:** Payment method references (bank name, code, account, icon)
- **Admin UI:** Next.js admin dashboard (18 pages) with Vietnamese labels, TanStack Table for data listing, react-hook-form + Zod validation
- **API Documentation:** Auto-generated OpenAPI docs at `/docs` (Swagger) and `/redoc` (ReDoc)
- **Database:** PostgreSQL 16, 31 tables, async SQLAlchemy 2.0, Alembic migrations
- **Deployment:** Docker Compose production stack (api + postgres + nginx), SSL via Certbot, gzip compression, nginx reverse proxy
- **Backup & Recovery:** Automated daily Postgres backups with 14-day rotation, rollback runbook
- **Testing:** Pytest suite with ≥70% coverage, async test support via pytest-asyncio
- **Seeding:** Idempotent seed scripts (content, packages, banks, superuser creation)

### Infrastructure
- **Stack:** FastAPI (Python 3.12), PostgreSQL 16, Nginx 1.27-alpine, Docker Compose
- **Frontend:** Next.js Pages Router, React 18, TypeScript 5, Tailwind CSS
- **File Storage:** Nginx volume mounts for `/media/` (PDFs, images) and `/static/` (future)
- **Authentication:** JWT (15min access token, 7day refresh), bcrypt password hashing, OAuth via Authlib

### Database Schema
- **Numerology Content:** 22 tables (attitude_number, balance_number, birthday_chart, birthday_number, challenge_life, deficit_number, development_number, execution_number, identifiable, introspective_number, karmic_number, main_number, mature_number, miss_number, mission_number, name_chart, peak_life, personal_month_number, personal_year_number, phone_number, souls_number, stages_of_life) + phone_master_data
- **Users & Auth:** users, user_profiles, refresh_tokens, social_accounts (4 tables)
- **Business:** packages, user_packages, user_payments, banks, news (5 tables)
- **Audit:** user_downloads (1 table)
- **Total:** 31 tables

### API Endpoints
- **Auth:** `/auth/register`, `/auth/login`, `/auth/refresh`, `/auth/logout`, `/auth/me`, `/auth/google`, `/auth/google/callback`, `/auth/facebook`, `/auth/facebook/callback` (9 endpoints)
- **Numerology:** `/api/so-hoc` (paid), `/api/so-hoc-free` (free), `/api/la-so` (horoscope), `/api/` (debug) (4 endpoints)
- **Profile:** `/profile/me` (GET/PUT), `/profile/birthday` (POST) (3 endpoints)
- **Content:** `/news`, `/news/{id}`, `/packages`, `/packages/{id}`, `/banks`, `/banks/{id}` (6 endpoints)
- **Payments:** `/payments` (POST/GET) (2 endpoints)
- **Admin:** `/admin/content/*` (23 resources, CRUD), `/admin/users/*`, `/admin/payments/*` (approve/reject), `/admin/upload` (15+ endpoints)
- **Health:** `/health` (1 endpoint)

### Breaking Changes
- **User Authentication:** All users must re-login after go-live (new JWT realm, old Django tokens invalid)
- **OAuth Callback URLs:** Google/Facebook console updated to point to FastAPI endpoints
- **Database:** Fresh PostgreSQL instance (no MySQL → Postgres ETL; seeded with placeholder content)
- **File Paths:** Media files served via Nginx (static mount), not Django media middleware

### Known Limitations
- PDF generation is synchronous (3-5s response time) — queue recommended post-launch
- Numerology content not cached (Redis integration planned for Q2)
- OAuth callback tokens passed in URL (HttpOnly cookie migration planned)
- No audit log for admin mutations (planned for Q2)
- No rate limiting (slowapi integration planned post-launch)
- Sentry error tracking not integrated (planned post-launch)

### Migration Notes
- **Cutover Window:** ~30 minutes (frontend update + DNS + service restart)
- **Rollback Window:** <10 minutes (database snapshot + DNS revert)
- **Data Loss Risk:** Zero (Postgres backup created pre-cutover)
- **Testing Conducted:** Numerology calc (all 9 number types), PDF generation, auth flows (JWT + OAuth), admin CRUD, deployment scripts

### Files Created/Modified
**Backend (numerology-api/):**
- New: app/core/numerology.py, app/core/numerology_sums.py, app/db/models/ (7 files), app/routers/ (9 routers), app/services/ (7 services), app/schemas/ (9 schemas), alembic/versions/ (2 migrations), tests/ (multiple suites), scripts/ (4 seed scripts), deploy/ (8 files)
- Modified: app/main.py, app/config.py, app/deps.py, pyproject.toml

**Frontend (Numerology-Landing-Page/):**
- New: src/pages/admin/ (18 pages), src/components/admin/ (8 components), src/lib/admin-* (3 libs)
- Modified: package.json (13 new deps), .env.example

### Phase Completion
✅ Phase 01: Project Setup  
✅ Phase 02: Database Models  
✅ Phase 03: Authentication  
✅ Phase 04: Numerology Calc + PDF  
✅ Phase 05: Content/Utility APIs  
✅ Phase 06: Admin UI  
✅ Phase 07: Seeding Scripts  
✅ Phase 08: Testing (≥70%)  
✅ Phase 09: Deployment  

### Next Steps
1. Deploy to production VPS
2. Execute cutover runbook (`deploy/cutover.md`)
3. Monitor for 24 hours (error rates, response times)
4. Announce to users (re-login required, new features available)
5. Post-launch tasks: Sentry, Redis cache, integration tests, audit log

---

## Future Releases (Planned)

### v1.1 (Q2 2026 — Post-Launch Week 4)
- [ ] Redis cache for numerology content reads
- [ ] Sentry error tracking + alerting
- [ ] Audit log for admin mutations
- [ ] Integration tests via PostgreSQL testcontainers
- [ ] Coverage increase to 80%
- [ ] Rate limiting (slowapi)

### v1.2 (Q3 2026)
- [ ] Mobile app (React Native) minimum viable product
- [ ] WebSocket support for real-time updates
- [ ] PDF generation queue (async, Celery optional)
- [ ] CDN integration for static/media files
- [ ] Prometheus metrics + Grafana dashboards

### v2.0 (2027+)
- [ ] Multi-tenancy (white-label support)
- [ ] Advanced analytics (user cohorts, conversion tracking)
- [ ] Machine learning (personalized number recommendations)

