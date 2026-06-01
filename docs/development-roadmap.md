# Development Roadmap

**Version:** 1.1  
**Last Updated:** 2026-05-26

---

## Phase Status (Migration Complete)

### Phase 01 — Project Setup & Docker Skeleton
**Status:** ✅ **Done**  
Setup: Python 3.12, FastAPI skeleton, Docker Compose (api + postgres), Alembic init, pytest config.

### Phase 02 — Database Models & Alembic
**Status:** ✅ **Done**  
31 tables: 22 numerology content, 4 user/auth, 5 business, 1 downloads. Migration: `0001_initial_schema.py`.

### Phase 03 — Authentication (JWT + OAuth)
**Status:** ✅ **Done**  
JWT (15min access, 7day refresh), Google/Facebook OAuth, superuser role, `/auth/*` endpoints.

### Phase 04 — Numerology Calc + PDF
**Status:** ✅ **Done**  
Calc: 9 number types, edge cases (master numbers, wraps). PDF: wkhtmltopdf + Jinja2 templates (invoice.html, invoice-free.html).

### Phase 05 — Content & Utility APIs
**Status:** ✅ **Done**  
CRUD for news, packages, banks. Payment tracking. User profile + quota mgmt. Admin CRUD routes (`/admin/content/*`).

### Phase 06 — Next.js Admin UI
**Status:** ✅ **Done**  
18 pages: content editor (TipTap), users, news, packages, banks, payments. TanStack Table, react-hook-form + Zod. Vietnamese labels.

### Phase 07 — Seeding Scripts
**Status:** ✅ **Done**  
`seed_content.py` (22 tables), `seed_packages.py`, `seed_banks.py`, `create_superuser.py`. Idempotent, safe to re-run.

### Phase 08 — Testing (Pytest ≥70%)
**Status:** ✅ **Done**  
Unit + integration tests: auth, numerology calc, endpoints, services. Coverage ≥70%.

### Phase 09 — Deployment (Docker Compose / Nginx)
**Status:** ✅ **Done**  
`docker-compose.prod.yml`, `nginx.conf` (SSL, gzip, reverse proxy), `deploy.sh`, `backup.sh`, cutover/rollback runbooks.

---

## Chatbot RAG (Future Feature — Phase 01 & 02 Complete)

### Chatbot RAG Phase 01 — Foundation (DB + Embedding + KB Ingestion)
**Status:** ✅ **Complete** (2026-05-26)
**Scope:** Database tables, Gemini embedding integration, knowledge base ingestion infrastructure (no user-facing endpoints yet).

**Deliverables:**
- 5 new ORM models (kb_documents, kb_chunks, chat_conversations, chat_messages, chat_quota_usage)
- Gemini text-embedding-004 service (batch, retry logic)
- Chunker service (tiktoken-based, 500-token windows)
- KbIngestionService (atomic upsert/reindex/delete)
- SQLAlchemy event listeners + asyncio worker queue (kb_sync)
- Alembic migration 0010 (pgvector extension, HNSW index)
- Backfill script (scripts/backfill_kb.py, --dry-run mode)
- 17 unit tests (all pass)
- Documentation updated (system-architecture.md, deployment-guide.md, project-changelog.md)

**Post-Review Fixes Applied (2026-05-26):**
- Phantom-doc race fixed: kb_sync now uses session `after_commit` / `after_rollback` (not mapper `after_insert`)
- Listener registration is now idempotent; `shutdown_kb_sync()` drains queue on lifespan teardown
- Retry classification uses typed HTTP status codes (no loose substring matches)
- Metadata columns unified to JSONB (kb_documents, kb_chunks, chat_messages.citations)
- chat_messages.created_at marked NOT NULL

---

### Chatbot RAG Phase 02 — Chat API Core (Retrieval + LLM Generation + Citations)
**Status:** ✅ **Complete** (2026-05-26)
**Scope:** 5 user-facing chat endpoints, RAG retrieval, Gemini LLM generation, citation extraction, anti-hallucination safeguards.

**Deliverables:**
- 6 new endpoints: POST/GET `/api/chat/conversations`, GET `/api/chat/conversations/{id}`, DELETE `/api/chat/conversations/{id}`, GET/POST `/api/chat/conversations/{id}/messages`
- RetrievalService (pgvector top-k cosine, free tier 3 chunks + 0.6 threshold, paid tier configurable)
- LlmService (Gemini Flash/Pro wrapper, 30s timeout, empty-response guard)
- PromptBuilder (anti-hallucination system prompt, user message sanitization, history max 5 turns)
- CitationParser (regex [N] extraction, bounds-check, dedup)
- ConversationService (CRUD, ownership 404 gate)
- 51 unit + integration tests (all pass)

**Post-Review Fixes Applied (2026-05-26):**
- **C1:** User message persists even on LLM 502 (commit before LLM call)
- **C2:** HTTP timeout bound via httpx on genai.Client (documented thread pool leak mitigation)
- **H8:** Retrieval exception skips LLM, returns canonical phrase directly
- **H12:** Empty/safety-blocked LLM response raises LlmError (not persisted as blank)

**Configuration Added:**
- RAG_TOP_K_FREE=3, RAG_TOP_K_PAID=8, RAG_SIM_THRESHOLD=0.6, HISTORY_MAX_MESSAGES=5, LLM_TIMEOUT_SECONDS=30

**Known Limitations (Documented):**
- Long transaction during 30s LLM call (acceptable for Phase 02, refactor in Phase 04 streaming)
- Thread pool completions on timeout may be slow but don't accumulate indefinitely with httpx timeout bound

---

### Chatbot RAG Phase 03 — User PDF Context (Hybrid Retrieval + TTL)
**Status:** ✅ **Complete** (2026-05-27)
**Scope:** User-uploaded PDFs attached to conversations, hybrid KB + PDF retrieval (PDF-favored split), 30-day TTL with nightly cleanup.

**Deliverables:**
- 2 new tables: user_pdf_index (SHA-256 hash, 30d TTL, UNIQUE per user), user_pdf_chunks (embeddings, HNSW index)
- 3 new endpoints: POST upload-pdf, PATCH pdf-context, DELETE pdf-context (all under `/api/chat/conversations/{id}`)
- PdfMatchService, PdfParserService, UserPdfService (orchestrate, race-safe, TTL slide)
- Hybrid retrieval merge (2 PDF + 1 KB on free tier when attached)
- Nightly cleanup job (03:00 UTC) expires + cascades; temp sweep
- Migration 0011 (pdf tables + chat_conversations.pdf_context_id FK)
- Backfill script (backfill_pdf_hashes.py, idempotent)
- 27 new tests (82 total pass; full suite 257/271)

**Post-Review Fixes Applied (2026-05-27):**
- **F1 — Streaming size check:** 1MB chunk-based read, 413 abort at 25MB (no full-body buffer). Nginx cap 26M for app contract.
- **F2 — KB/PDF split documented:** Intentional PDF-favor (user intent); over-budget fix (skip KB when kb_k==0).
- **F3 — Atomic insert race:** IntegrityError caught, re-query + TTL slide; user gets success not 500.
- **F5 — TTL slide on re-upload:** Re-upload bumps expires_at to now() + 30d (active PDFs survive day 30).
- **F6 — PDF citation filenames:** JOIN user_pdf_index.filename → "report.pdf/p4" not "user_pdf/4".

**Configuration Added:**
- USER_PDF_TTL_DAYS=30, USER_PDF_MAX_BYTES=26214400, PDF_CHUNK_TOKEN_WINDOW=500, PDF_CHUNK_OVERLAP_TOKENS=50
- nginx: client_max_body_size 26M

**Known Limitations:**
- Cleanup-job race window (edge case): expired PDF deleted between SELECT and re-upload insert (rare; new row gets fresh TTL)
- Hash trust on disk: stale file_hash if user_reports.pdf_path regenerated (low likelihood; no write hook enforces)

**Dependencies:**
- pypdf>=4.0 added

---

---

### Chatbot RAG Phase 08 — Chatbot Hardening + Launch Readiness (Cost Monitor, Abuse Detection, CAPTCHA, Feature Flags, A/B Testing, DSAR)
**Status:** ✅ **Complete** (2026-05-28)
**Scope:** Production hardening, cost controls, abuse prevention, compliance (DSAR endpoint), feature rollout infrastructure. 39 new tests. 3 ops docs created.

**Backend Deliverables:**
- **Services:** CostMonitorService (token cost calculation, alerts on thresholds), AbuseDetectionService (5 patterns: rate spike, prompt injection, resource exhaustion, jailbreak, toxicity), FeatureFlagService (rollout %, per-user override), AbTestService (A/B variant assignment, Gemini LLM switching)
- **Endpoints:** DELETE `/api/profile/chat-data` (DSAR — user chat data wipe), GET `/admin/chatbot/cost-monitor` (cost trends), POST `/admin/chatbot/feature-flags` (create/update flag)
- **Models:** cost_monitor_events, abuse_detection_logs, feature_flags, ab_test_assignments (Migration 0015)
- **Router:** _hardening_gate.py (run_hardening_gates middleware; blocks request if abuse detected or feature disabled)
- **Jobs:** aggregate_chat_metrics (nightly cost summary), detect_chat_abuse (continuous abuse pattern detection)
- **CAPTCHA:** Turnstile integration on chat start (configurable per rollout %)
- **Config:** COST_MONITOR_ALERT_THRESHOLD, ABUSE_PATTERN_*, FEATURE_FLAG_ROLLOUT_%, LLM_AB_TEST_ENABLED

**Ops Docs Created:**
- `docs/chatbot-runbook.md` — operational procedures, deployment checklist, incident playbooks
- `docs/chatbot-launch-checklist.md` — pre-flight items, monitoring setup, rollout phases
- `docs/chatbot-cost-monitoring.md` — cost tracking, alert configuration, budget forecasting

**Tests:** 39 new tests (cost monitor, abuse detection, feature flags, A/B variants, DSAR endpoint, hardening gate)

**Known Limitations:**
- Abuse pattern detection: heuristic-based (ML models deferred to Phase 09+)
- DSAR wipe: soft-delete with 30d recovery window (hard delete on request)

---

### Chatbot RAG Phase 07 — Admin Chatbot Tuning (KB Upload, Prompt Override, Conversation Browser, Analytics)
**Status:** ✅ **Complete** (2026-05-28)
**Scope:** Admin KB ingestion, system prompt override with audit trail, conversation filtering, manual addon grants, usage analytics.

**Backend Deliverables (COMPLETE):**
- Services: AdminKbService (PDF/DOCX/TXT/MD extraction), PromptSettingsService (60s TTL cache + audit log), ChatAnalyticsService (SQL aggregations)
- Router: `/admin/chatbot/*` (10 endpoints: KB CRUD, prompt editor, conversation browser, analytics, addon grants)
- Models: chat_system_settings, chat_system_settings_history (Migration 0014)
- Hybrid prompt: In-code default + override logic centralized in resolve_system_prompt()
- Dependencies: python-docx>=1.1
- Tests: All pass (comprehensive admin endpoints coverage)

**Frontend Deliverables (PARTIAL):**
- Pages: `/admin/chatbot` (dashboard stub), `/admin/chatbot/kb` (KB upload + document list)
- Components: kb-upload-form.tsx, kb-document-list.tsx, chatbot-types.ts
- Navigation: "Chatbot RAG" group added
- Deferred: Prompt editor UI, conversation browser UI, analytics dashboard (Phase 08)

**Post-Review (if conducted):** Pending

**Known Limitations:**
- Frontend UI incomplete (functional backend ready for integration)
- Admin runbook deferred to Phase 08

---

### Chatbot RAG Phase 06 — Semantic Cache + Rate Limiting (Optimization + Abuse Prevention)
**Status:** ✅ **Complete** (2026-05-28) — **Superseded by DeepSeek migration (2026-06-01)**
**Scope:** Optimize cost (semantic cache 24h) + prevent abuse (two-bucket rate limiting with fail-closed policy). Prompt caching removed after LLM migration to DeepSeek (server-side auto-caching). 345→335 tests pass (prompt cache tests removed).

**Backend Deliverables:**
- Services: SemanticCacheService (pgvector cosine ≥0.92, tier-scoped, 24h TTL, NO_INFO exclusion), RateLimitService (two-bucket atomic user+IP, fail-closed, Asia/Bangkok daily reset)
- Models: SemanticCacheEntry, RateLimitBucket tables
- Routers: Pipeline integrated into existing /api/chat/conversations/{id}/messages + stream (rate limit → quota → retrieval → semantic cache → LLM → cache insert)
- Jobs: cleanup_semantic_cache.run() nightly 03:15 UTC
- Modified: messages.py (pipeline ordering), _stream_generator.py (stream variant), llm_service.py (DeepSeek via OpenAI SDK)
- Migration 0013: 2 new tables + HNSW index (pgvector ≥0.5.0 required)
- Tests: 335 total pass, 0 failed. Ruff + tsc + lint clean.

**Frontend Deliverables:**
- Hook: use-rate-limit-countdown (countdown display on message input)
- Modified: MessageInput (send button disable during lockout), use-chat-stream (HTTP 429 handler, Retry-After parsing)
- Toasts: Sonner variants bucket_empty (warn, 3s), daily_cap (error, 8s)

**Configuration:**
- No new env vars (all settings-backed: SEMANTIC_CACHE_THRESHOLD=0.92, SEMANTIC_CACHE_TTL_HOURS=24)
- Removed env vars: PROMPT_CACHE_HIT_THRESHOLD, PROMPT_CACHE_TTL_SECONDS (DeepSeek migration, 2026-06-01)

**Code Review (3 Critical + 10 High + 10 Medium):**
- **C1:** Prompt-cache invalidation fires on every KB sync (defeats cost savings). Fix: hash content in _replace_chunks
- **C2:** daily_cap TZ mismatch (UTC midnight vs Asia/Bangkok 07:00 local). Spec: decide UTC or Bangkok
- **C3:** Rate-limit lock held during LLM (DB pool risk, 5s+). Acceptable? Alternative: commit early
- **H1:** Fail-open policy (NOW: fail-closed for unknown exceptions)
- **H2–H10:** Cleanup isolation, ensure_bucket optimization, race conditions, file size guidelines, SSE docs (selectively addressed)

**Known Limitations (Escalated for Lead Decision):**
- **C1 KB invalidation:** Prompt cache removed (DeepSeek migration 2026-06-01). Limitation no longer applies.
- **C2 TZ ambiguity:** Daily reset at UTC (current). Users in VN see 07:00 local. Document choice explicitly
- **C3 lock duration:** Rate-limit lock held until request end (5s+ during LLM). Acceptable for v1? Consider session-early-commit

**Next:** Phase 07 (Address C2 TZ decision, C3 lock refactor if needed)

---

### Chatbot RAG Phase 05 — Chat Quota + Add-on Packages (Monetization)
**Status:** ✅ **Complete** (2026-05-28)
**Scope:** Per-message quotas (free 3/day), purchasable message packs (Flash/Pro tiers, 30d validity), SePay webhook auto-fulfillment.

**Backend Deliverables:**
- Services: QuotaService (check/decrement, atomic SELECT FOR UPDATE on addon + ON CONFLICT on free), addon_fulfillment.fulfill_chat_addon (idempotent)
- Routers: /api/chat/addons (GET list, POST purchase), /api/chat/quota (GET user quota)
- Models: ChatAddonPurchase, AddonPackageOut, QuotaOut, QuotaDecision, QuotaConflictError
- Migration 0012: chat_addon_purchases table + packages(package_kind, message_count, tier, validity_days) columns
- Modified: messages.py (quota gate + sync decrement), _stream_generator.py (pre-commit decrement), payment_service.py (branched on package_kind)
- SePay webhook: Extended matcher for CHATADDON<id> content prefix (auto-fulfillment of chat addons)
- Tests: 290 total pass, 0 failed; tsc + lint clean

**Frontend Deliverables:**
- Components: QuotaBadge (remaining quota + tier), UpsellModal (bank info + polling after purchase)
- Pages: /chat/upgrade (AddonList + AddonCard)
- Hooks: use-quota (polling 10s default, 5min cap)
- Modified: ChatLayout (quota display + upsell trigger), use-chat-stream (onQuotaExceeded callback, 402 + SSE quota_exceeded handling)
- Admin: package form +package_kind selector + conditional ChatAddonFields with zod validation

**Configuration:**
- No new env vars (reuses existing GEMINI_API_KEY, etc.)

**Known Issues (Deferred to Phase 06):**
- **C1:** SePay webhook path incomplete — UserPayment created but webhook doesn't call fulfillment until matcher extended (workaround: manual admin approval)
- **C2:** Stream decrement race — happens after commit; client disconnect window. Fix: move inside transaction pre-commit
- **H3:** No polling on /chat/upgrade — user must navigate away to see quota refresh. Fix: add 5-10s poll on purchase completion

**Next:** Phase 06 (Fix C1/C2/H3, quota polling, payment status UI)

---

### Chatbot RAG Phase 04 — Streaming Chat UI & Backend (SSE + Full Chat Interface)
**Status:** ✅ **Complete** (2026-05-27)
**Scope:** Server-Sent Events streaming endpoint, full Next.js /chat UI with conversations, messages, citations, PDF upload.

**Backend Deliverables:**
- New modules: sse_formatter.py (33 LOC), chat_turn.py (97 LOC split from messages.py), _stream_generator.py (120 LOC)
- Modified: llm_service.py (+83 LOC: StreamResult, generate_stream), messages.py (rewritten 185 LOC)
- SSE endpoint POST `/api/chat/conversations/{id}/messages/stream` with events: delta, citations, done, error
- Ownership check + user message persist before generator starts (404/422 normal HTTP)
- Retrieval failure: emit canonical "Tôi không có đủ thông tin..." phrase (no LLM call)
- Mid-stream LLM error: emit error event; no broken assistant row committed
- Tests: 40 pass (13 new stream tests: happy-path 7, retrieval-fail 1, llm-error 2, auth/ownership 3)

**Frontend Deliverables:**
- Page: src/pages/chat.tsx (52 LOC, auth guard → /login)
- Module: src/modules/chat/ (13 files, 1,342 LOC total)
  - API: chat-api.ts (100 LOC, CRUD + PDF)
  - Hooks: use-conversations.ts (62), use-messages.ts (48), use-chat-stream.ts (228 SSE consumer), use-pdf-upload.ts (58)
  - Parts: MessageMarkdown.tsx (88), CitationDrawer.tsx (78), PdfUploadButton.tsx (82), ConversationSidebar.tsx (96), MessageInput.tsx (118), MessageThread.tsx (204), ChatLayout.tsx (204)
- Packages: react-markdown, remark-gfm, rehype-sanitize added
- Header.tsx: Added "Chat AI" button/menu (authenticated-only)
- TypeScript: zero errors; ESLint: zero errors; Build: clean

**Configuration:**
- No new env vars (reuses GEMINI_API_KEY, LLM_TIMEOUT_SECONDS, etc. from Phase 02+03)

**Nginx Configuration:**
- SSE location regex: `^/api/chat/conversations/\d+/messages/stream$`
- Directives: proxy_buffering off, gzip off, proxy_read_timeout 300s, X-Accel-Buffering: no

**Known Limitations:**
- use-chat-stream.ts: First-token timeout (self._timeout) applied only to first SSE event; subsequent pauses unbounded until nginx timeout (300s). Per-token watchdog deferred (nginx timeout sufficient for now).
- Mid-stream LLM error: Partial tokens already shown in browser; no partial assistant row persisted. Clean DB but orphaned UI tokens. Phase 05+ may add partial error state.
- Citation drawer: Backend SSE citations event lacks chunk_text; only metadata shown (index, title, source_type, score).

**Next:** Phase 05 (Quota tracking per month, paid tier LLM switching)

---

## Post-Launch (Next 30 Days)

### Launch Readiness Phase 01+02
**Status:** ✅ **Implemented 2026-05-26**
- Legal pages (4 SSG): terms, privacy (NĐ13/2023), refund-policy, contact
- Cookie consent banner (localStorage 365d, NĐ13 compliant)
- GA4 + Meta Pixel with consent gating
- SEO: next-sitemap, robots.txt, manifest.json, canonical/OG/Twitter meta
- Payment refund flow: POST `/admin/orders/{id}/refund` + signed download links
- SePay reconciliation cron (15min, idempotent via webhook dedup)
- Sentry skeleton (Next.js + FastAPI) with PII scrubber
- Docs: analytics-events, legal-content-sources, payment-incident runbook

### Launch Readiness Phase 04
**Status:** ✅ **Implemented 2026-05-26**
- Admin ops: Order search (email ILIKE partial, ref_code, status, date_from/to, pagination), CSV export (10k row max, UTF-8 BOM, formula-injection sanitized)
- Frontend: order-search-form component (Bangkok TZ +07:00 contract, "Xóa lọc" reset, "Xuất CSV" button), /admin/orders rewritten with pagination + empty state
- SEO: img alt text fixes (3 images), next/image migration (bg-teacher 627KB, adalash_banner 317KB with LCP priority), image audit created (10 tags tracked, 6 deferred, 4 CSS bg ~5.6MB)
- Runbooks: go-live-runbook.md (pre-flight 16 items, deploy 12 steps, rollback, comms), post-launch-monitoring.md (daily/weekly checks, alert thresholds, escalation)
- Fixes: C1 http_http_status typo, H1 ILIKE wildcard escape, H2 CSV formula injection, H3 DatePicker TZ, H5 JSON error UX
- Tests: 173/190 pass (17 pre-existing unchanged, 0 regressions), frontend build clean
- Docs: go-live-runbook.md, post-launch-monitoring.md, image-audit.md, codebase-summary.md v1.4 update

### Plan Status
**Launch Readiness Checklist:** Code implementation phases 01-04 complete. Functional code ship ready. Pending user external actions (DNS/registrar setup, API signups, blog content, mobile QA, legal placeholders, favicon assets).

---

### Launch Readiness Phase 03
**Status:** ✅ **Implemented 2026-05-26**
- Security: slowapi rate limiting (login 5/min, register 3/min, forgot-password 3/min IP+email, webhook 100/min), Cloudflare Turnstile CAPTCHA (backend verify fail-closed, frontend dev-skip guarded), Nginx security headers (HSTS 2yr, XFO, XCTO, Referrer-Policy, Permissions-Policy, CSP)
- Email deliverability: 4 plain-text fallbacks + 2 refund pair (welcome/password-reset/quota-low/order-expired + order-paid/order-refund), base.html unsubscribe footer via Jinja inheritance, multipart text+html dispatch
- UX: FAQ 15 Q&A 3 groups SSG, Hướng dẫn sử dụng 5-step SSG, generic empty-state component, 3 skeleton loaders (order/report/shop cards), my-account orders/reports proper empty states
- Config cleanup: next.config.js OAuth env vars removed, NEXT_PUBLIC_TURNSTILE_SITE_KEY added, ignore flags retained with lint-cleanup-backlog.md reference
- Tests: 173/190 pass (17 pre-existing admin failures unchanged, +3 auth register tests pass)
- Docs: lint-cleanup-backlog.md deferred Phase 04 admin cleanup

---

### Sentry Error Tracking
**Status:** Partially Done  
**Notes:** Config skeleton + PII scrubber xong. User must sign up free.sentry.io + set SENTRY_DSN env var.

---

### Integration Tests via PostgreSQL Testcontainers
**Priority:** High  
**Effort:** M  
**Goal:** Replace fixtures with real containerized Postgres in CI; run full API test suite against live DB.

**Tasks:**
- [ ] Add `testcontainers` library (Python)
- [ ] Create fixture: `@pytest.fixture(scope="session") async def postgres_container()`
- [ ] Rewrite conftest.py to use containerized DB (vs in-memory mock)
- [ ] Run pytest with container startup/cleanup
- [ ] Integrate into CI/CD pipeline

**Files to Create/Modify:**
- `tests/conftest.py` (add container fixture)
- `pyproject.toml` (add testcontainers dep)
- `.github/workflows/tests.yml` (if CI added)

---

### Increase Test Coverage to 80%
**Priority:** High  
**Effort:** M  
**Goal:** Reach 80% code coverage (currently ~70%).

**Gap Areas:**
- Admin payment approval edge cases (reject workflow)
- Horoscope API timeout/partial failure scenarios
- OAuth callback error handling (invalid state, token exchange failure)
- Numerology calc: all 9 numbers (some untested edge cases)
- File upload validation (MIME, size overflow)

**Tasks:**
- [ ] Add coverage report to CI: `pytest --cov=app --cov-report=html`
- [ ] Identify uncovered branches: `coverage report`
- [ ] Write tests for identified gaps
- [ ] Target: ≥80% overall

---

### Redis Cache for Content Reads
**Priority:** Medium  
**Effort:** M  
**Goal:** Reduce DB joins for numerology content (22 tables, read-heavy).

**Implementation:**
- Cache numerology content by (table, code, number) for 24h
- TTL: 86400s (1 day)
- Invalidation: Admin updates content → cache bust key
- Fallback: If Redis unavailable, query DB directly

**Tasks:**
- [ ] Add `redis` and `aioredis` to dependencies
- [ ] Create `app/services/cache_service.py`
- [ ] Add `@cache_decorator(ttl=86400)` to `numerology_db.fetch_by_code()`
- [ ] Invalidation hook in admin content update route
- [ ] Test cache hit/miss behavior
- [ ] Add to docker-compose.prod.yml

**Files to Create/Modify:**
- `app/services/cache_service.py` (new)
- `app/config.py` (add REDIS_URL)
- `docker-compose.prod.yml` (add redis service)
- `.env.example` (add REDIS_URL)

---

### Sentry Error Tracking
**Priority:** Medium  
**Effort:** S  
**Goal:** Real-time error alerts + stack trace collection.

**Implementation:**
- Initialize Sentry SDK in `app/main.py`
- Capture all unhandled exceptions
- Optional: performance monitoring (slow requests)

**Tasks:**
- [ ] Create Sentry project (sentry.io)
- [ ] Add `sentry-sdk` to dependencies
- [ ] Initialize in main.py: `sentry_sdk.init(dsn=settings.SENTRY_DSN, ...)`
- [ ] Test: trigger error, verify in Sentry dashboard
- [ ] Add SENTRY_DSN to .env.prod

**Files to Modify:**
- `app/main.py` (add Sentry init)
- `app/config.py` (add SENTRY_DSN setting)
- `pyproject.toml` (add sentry-sdk)

---

### Audit Log for Admin Mutations
**Priority:** Medium  
**Effort:** M  
**Goal:** Track all admin data changes (content edits, payment approvals, user updates).

**Schema:**
```sql
CREATE TABLE audit_log (
  id BIGSERIAL PRIMARY KEY,
  admin_user_id BIGINT NOT NULL REFERENCES users(id),
  action VARCHAR(50),  -- CREATE, UPDATE, DELETE, APPROVE, REJECT
  table_name VARCHAR(100),
  record_id BIGINT,
  old_values JSONB,
  new_values JSONB,
  created_at TIMESTAMPTZ SERVER DEFAULT now()
);
```

**Implementation:**
- Middleware: intercept all admin route requests (POST/PUT/DELETE)
- Log before/after state
- Query: `SELECT * FROM audit_log WHERE admin_user_id = ? ORDER BY created_at DESC`

**Tasks:**
- [ ] Create migration: `0003_add_audit_log_table.py`
- [ ] Add `AuditLog` model
- [ ] Create `AuditLogService` for logging
- [ ] Add middleware in `app/main.py`
- [ ] Create `/admin/audit-log` endpoint (read-only)
- [ ] Test: edit content, verify audit entry created

**Files to Create/Modify:**
- `alembic/versions/0003_add_audit_log_table.py` (new migration)
- `app/db/models/audit.py` (new model)
- `app/services/audit_service.py` (new service)
- `app/routers/admin/audit.py` (new endpoint)
- `app/main.py` (add middleware)

---

### Rate Limiting & API Throttling
**Status:** ✅ **Implemented 2026-05-26**  
**Implementation:**
- Backend: slowapi middleware with CF-Connecting-IP priority + `trusted_proxy_mode` setting (Cloudflare vs direct nginx)
- Rate limits: `/login` 5/min, `/register` 3/min, `/forgot-password` 3/min IP+email, `/webhooks/sepay` 100/min
- In-memory storage (per-worker: gunicorn `-w 4` = 4× effective limit); Redis backend available on scale-up
- Test bypass: `Limiter(enabled=settings.rate_limit_enabled)` allows tests to disable
- Decorators: `@limiter.limit()` on auth + webhook endpoints, rate limit fired before handler body

**Known Limitations:**
- In-memory storage resets on uvicorn restart; per-worker isolation means effective limit = `worker_count × configured_limit`
- Mitigation: document limitation, upgrade to Redis (`storage_uri="redis://..."`) before high-traffic scale

**Files:**
- `app/middleware/rate_limit.py` (created)
- `app/config.py` (added RATE_LIMIT_ENABLED, TRUSTED_PROXY_MODE settings)
- `app/routers/auth.py` (added @limiter decorators to login/register/forgot-password)
- `app/main.py` (mounted SlowAPIMiddleware)

---

## Pending User Actions Before Public Launch

All Phase 01-04 code implementation complete. The following external dependencies **must be resolved by user/ops team** before go-live:

| Action | Owner | Status | Notes |
|--------|-------|--------|-------|
| **DNS & Domain Setup** | Ops | TODO | Point domain DNS to Cloudflare; enable proxy; confirm via SSL Labs scan |
| **Cloudflare Turnstile** | Ops | TODO | Signup, obtain site key + secret key, enable in production |
| **Resend + Google Gmail** | Ops | TODO | Create Resend account, generate API key, configure SPF/DKIM |
| **Sentry Error Tracking** | Ops | TODO | Signup free.sentry.io, create project, set SENTRY_DSN env var |
| **UptimeRobot Monitoring** | Ops | TODO | Setup uptime checks + alert contacts |
| **Blog Content (5-10 bài)** | Content | TODO | Create via admin News CRUD interface |
| **Mobile QA** | QA | TODO | Real device testing (iOS + Android) |
| **Mail-Tester Verification** | Ops | TODO | Send test emails, verify deliverability |
| **Favicon & Assets** | Design | TODO | Generate favicon.ico, apple-touch-icon.png, og-default.png |
| **Legal Placeholders** | Legal/Content | TODO | Fill [BRACKETS] in /terms, /privacy, /refund-policy, /contact (DN, MST, address, phone, Zalo OA) |
| **Final E2E Smoke Test** | QA | TODO | User flow: register → login → search → payment → PDF |
| **Soft Launch Beta** | Ops | TODO | Invite list, gather feedback, iterate |
| **Enable Ads** | Marketing | TODO | Google Ads, Meta Pixel event tracking live |

**See:** `docs/go-live-runbook.md` for pre-flight checklist (16 items) + deploy steps (12 steps).

---

## Q3+ (Future, Beyond Launch)

### Mobile App (React Native or Flutter)
**Priority:** P1 (high revenue driver)  
**Effort:** L  
**Timeline:** Q3 2026+  
**Notes:** Reuse existing API (`/api/so-hoc`, `/auth/*, /profile/*`). No new backend endpoints needed.

**Architecture:**
- Separate repo: `numerology-mobile`
- Backend: Same FastAPI (add `User-Agent` header detection for mobile)
- Auth: JWT + refresh token (same as web)
- Payments: In-app purchase (Google Play, App Store) → backend payment approval flow

---

### Real-Time Features (WebSocket)
**Priority:** P2 (nice-to-have)  
**Effort:** M  
**Timeline:** Q4 2026+  
**Use Cases:**
- Notify admin when payment received (real-time approval prompt)
- Notify user when PDF ready (if async queue added)
- Live content editor collab (multiple admins editing simultaneously)

**Architecture:**
- FastAPI WebSocket support (already supports via `@app.websocket`)
- Redis pub/sub for distributed messaging (multi-instance)
- Client: socket.io or native WebSocket

---

### Multi-Tenancy (Per Plan: Out-of-Scope)
**Priority:** P3 (future expansion)  
**Effort:** L  
**Timeline:** 2027+  
**Concept:** Multiple organizations/brands using same platform (white-label).

**Schema Changes:**
- Add `tenant_id` (UUID) to all data tables
- Separate schema-per-tenant (alternative: row-level security)
- OAuth: per-tenant client credentials

**Status:** Marked as out-of-scope for initial launch.

---

## Known Limitations & Tech Debt

| Item | Impact | Priority | Note |
|------|--------|----------|------|
| PDF render sync (not queued) | Slow requests (3-5s) | P2 | Consider Celery queue post-launch |
| No caching (numerology content) | DB joins every request | P2 | Redis cache planned (see roadmap) |
| OAuth callback via URL token | Security risk (URL logs) | P2 | Migrate to HttpOnly cookie post-launch |
| No audit log (admin changes) | Compliance gap | P3 | Planned for Q2 |
| Django → FastAPI re-login required | UX friction | Done | Communicated at cutover |
| wkhtmltopdf subprocess (no containerization) | Version mismatch risk | P3 | Consider Playwright HTML-to-PDF alternative |
| No monitoring/alerting | Blind prod ops | P1 | Sentry + Prometheus planned |
| Static/media serving via Nginx volume | Not CDN'd | P3 | Add Cloudflare CDN post-launch |
| Rate limiting in-memory storage | Per-worker isolation; restart resets | P3 | Scale to Redis before 10k rps; Phase 03 documented limitation |
| Sentry skeleton | Config only; requires DSN + user signup | P2 | Partially Done (Phase 02) |
| Admin lint errors (100+) | Build warning, hidden by ignore flags | P2 | Deferred to Phase 04+ cleanup sprint per lint-cleanup-backlog.md |
| Image alt text & optimization | 3 fixed Phase 04, 6 deferred, ~5.6MB CSS bg unaddressed | P3 | See docs/image-audit.md; Cloudflare Polish or manual WebP post-launch |

---

## CI/CD Roadmap (Post-Launch)

### Phase 1: Basic Testing (Week 1 Post-Launch)
- [ ] GitHub Actions workflow: `pytest` on every PR
- [ ] Coverage report: `--cov=app --cov-report=term-missing`
- [ ] Status badge in README

### Phase 2: Automated Deployment (Week 2-3)
- [ ] Auto-deploy on git tag: `git tag v1.0.1` → build → test → deploy
- [ ] Rollback trigger: manual button in GitHub Actions

### Phase 3: Advanced Monitoring (Month 2)
- [ ] Prometheus metrics export from FastAPI
- [ ] Grafana dashboards (response time, error rate, DB connections)
- [ ] Alerting: PagerDuty integration (500 errors, high latency)

---

## Success Metrics (Post-Launch)

| Metric | Target | Tracking |
|--------|--------|----------|
| **Availability** | 99.5% uptime | UptimeRobot |
| **Performance** | 95th percentile <500ms (excl. PDF) | Sentry, Prometheus |
| **Error Rate** | <0.5% 5xx errors | Sentry dashboard |
| **Test Coverage** | ≥80% | Coverage reports in CI |
| **Deployment Time** | <5min per deploy | CI logs |
| **Backup Success** | 100% daily backups | Cron job logs |
| **Admin UI UX** | <2s page load | Lighthouse |

---

## Dependencies & Risk Mitigation

### High-Risk Dependencies (Monitor for Updates)

| Dep | Risk | Mitigation |
|-----|------|-----------|
| wkhtmltopdf | Unmaintained, version mismatch | Switch to Playwright (P3) |
| FastAPI | Low risk, actively maintained | Auto-update patch versions |
| PostgreSQL 16 | EOL in 2028 | Plan migration to PG 17+ in 2027 |
| Node 18 | EOL in 2025, upgrade to 20+ | Next.js 15+ requires Node 18+ |

---

## Maintenance Schedule

**Weekly:**
- Monitor Sentry (once added) for new error patterns
- Check backup success logs
- Review slow query logs (if RDS monitoring added)

**Monthly:**
- Review nginx.conf + docker-compose.prod.yml for config drift
- Audit user counts, API request volume
- Plan next month's tasks

**Quarterly:**
- Database health check (bloat, index usage)
- Dependency updates (mypy, pytest, etc.)
- Review roadmap vs. actuals, adjust timeline

