# System Architecture

**Document Version:** 1.1  
**Last Updated:** 2026-05-26

---

## High-Level Architecture

```
                        ┌─────────────────────────────┐
                        │  Next.js Frontend + Admin   │
                        │  (Numerology-Landing-Page)  │
                        └──────────────┬──────────────┘
                                       │ HTTPS (Bearer JWT)
                                       ▼
                        ┌─────────────────────────────┐
                        │   Nginx (Reverse Proxy)     │
                        │   SSL, Gzip, Rate Limit     │
                        └──────────────┬──────────────┘
                                       │
                    ┌──────────────────┼──────────────────┐
                    ▼                  ▼                  ▼
            ┌──────────────┐   ┌──────────────┐  ┌──────────────┐
            │   FastAPI    │   │ Static/Media │  │   Certbot    │
            │   (Gunicorn) │   │   (Nginx)    │  │  (Auto SSL)  │
            │  Port 8000   │   │              │  │              │
            └──────┬───────┘   └──────────────┘  └──────────────┘
                   │
        ┌──────────┴──────────┐
        ▼                     ▼
  ┌────────────────┐   ┌──────────────┐
  │ PostgreSQL 16  │   │ Media Volume │
  │ (Async Driver) │   │ (PDFs, JPGs) │
  │ (31 tables)    │   │              │
  └────────────────┘   └──────────────┘
```

---

## Component Details

### 1. FastAPI Service (`numerology-api/`)

**Stack:** Python 3.12, FastAPI 0.115+, SQLAlchemy 2.0, Pydantic v2

**Entry Point:** `app/main.py`  
- CORS config (frontend domain)
- Router registration (auth, numerology, profile, admin, etc.)
- Middleware: logging, exception handlers
- Health check: `GET /health` → `{"status": "ok"}`

**Directory Structure:**
```
app/
├── main.py              # FastAPI factory
├── config.py            # Pydantic settings (env vars)
├── deps.py              # Dependency injection (get_db, get_current_user, get_current_superuser)
├── db/
│   ├── base.py          # SQLAlchemy DeclarativeBase
│   ├── session.py       # Async engine + sessionmaker
│   └── models/          # ORM models (31 tables)
│       ├── mixins.py    # TimestampMixin, etc.
│       ├── user.py      # users, user_profiles, user_downloads
│       ├── auth.py      # refresh_tokens, social_accounts
│       ├── numerology_content.py  # 22 content tables
│       ├── package.py   # packages, user_packages, user_payments
│       └── news.py      # news table
├── core/
│   ├── security.py      # Password hashing, JWT functions (jti on refresh)
│   ├── numerology.py    # Main calculation logic (170 LOC)
│   ├── numerology_sums.py # Sum helpers
│   └── alphabet.py      # Vietnamese accents + strip_accents
├── routers/             # APIRouter per resource (12+ endpoints)
│   ├── auth.py          # /auth/* (register, login, refresh, forgot/reset password)
│   ├── numerology_free.py   # /api/so-hoc-free, /api/la-so
│   ├── numerology_paid.py   # /api/so-hoc (quota-gated, PDF download)
│   ├── numerology.py    # Assembly (includes free + paid)
│   ├── profile.py       # /profile/* (me, birthday, quota)
│   ├── news.py          # /news/* (list, detail)
│   ├── packages.py      # /packages/* (list, detail)
│   ├── banks.py         # /banks/*
│   ├── payments.py      # /payments/* (list, detail)
│   └── admin/           # Admin CRUD
│       ├── content.py   # /admin/content/* (all 23 numerology tables)
│       ├── users.py     # /admin/users/*
│       ├── payments.py  # /admin/payments/* (approve/reject)
│       └── uploads.py   # /admin/upload (image/file)
├── services/            # Business logic
│   ├── user_service.py      # User CRUD, password updates
│   ├── token_service.py     # JWT/refresh token creation (tz-aware compare)
│   ├── password_reset_service.py # One-time hashed reset tokens
│   ├── email_service.py     # SMTP send w/ log fallback
│   ├── numerology_service.py # Facade for calc
│   ├── numerology_db.py     # DB fetch (numerology content)
│   ├── numerology_context.py # Context building, quota decrement
│   ├── horoscope_client.py  # Async httpx → vietheart.net
│   ├── upload_service.py    # File upload validation
│   └── payment_service.py   # Payment approval workflow
├── schemas/             # Pydantic v2 models (request/response)
│   ├── auth.py          # TokenOut, LoginRequest, etc.
│   ├── numerology.py    # SoHocQuery, LasoQuery, CalcResponse
│   ├── profile.py       # UserOut, ProfileUpdate
│   ├── content.py       # ContentCreate, ContentUpdate (23 variants)
│   ├── payment.py       # PaymentApprovalRequest, PaymentOut
│   └── common.py        # Pagination, Error, etc.
├── utils/
│   ├── pdf.py           # render_html() + render_pdf() (Jinja2 → wkhtmltopdf)
│   └── pagination.py    # PaginationParams, paginate()
└── templates/           # Jinja2 HTML
    ├── invoice.html     # Paid PDF template
    └── invoice-free.html # Free PDF template
```

### 2. PostgreSQL 16 Database (Existing Content & Auth)

**Schema:** 36 tables (31 original + 5 KB/chat tables from Phase 01; post-migration, fresh start from Django; `social_accounts` dropped + `password_reset_tokens` added on 2026-05-25)

| Category | Tables | Purpose |
|----------|--------|---------|
| **Numerology Content** (22) | attitude_number, balance_number, birthday_chart, birthday_number, challenge_life, deficit_number, development_number, execution_number, identifiable, introspective_number, karmic_number, main_number*, mature_number, miss_number, mission_number, name_chart, peak_life, personal_month_number, personal_year_number, phone_number, souls_number, stages_of_life | User-facing content, editable via admin |
| **User & Auth** (4) | users, user_profiles, refresh_tokens, password_reset_tokens | Account mgmt, JWT tokens, one-time reset tokens |
| **Business** (5) | packages, user_packages, user_payments, banks, news | Subscriptions, payment tracking, news articles |
| **Downloads** (1) | user_downloads | Audit log (user, type, timestamp, content) |

*main_number: extra columns content_2, content_3, content_4, content_5

**Key Constraints:**
- `users.email` UNIQUE
- `user_profiles` 1-1 FK to users (CASCADE delete)
- `user_downloads.type` CHECK IN (0, 1) — 0=free, 1=paid
- `refresh_tokens.token_hash` UNIQUE + indexed
- `password_reset_tokens.token_hash` UNIQUE + indexed (SHA-256 of raw token); `used_at` + `expires_at` enforce single-use, 30-min TTL

### 2a. Knowledge Base & Chat (Chatbot RAG Foundation — Phase 01)

**Purpose:** Store embeddings, chunks, conversations, quota usage for future RAG-based chatbot.

**Tables:** 5 new tables (migration `0010_chatbot_foundation.py`; pgvector extension auto-installed)

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `kb_documents` | Source documents (numerology content) | `source_type` (enum: main_number, attitude_number, etc.), `source_ref` (integer), `title`, `content`, `metadata` (JSON), natural key `(source_type, source_ref)` |
| `kb_chunks` | Text chunks with 768-dim embeddings | `document_id` (FK), `chunk_index`, `content` (text), `token_count`, `embedding` (Vector(768)), `metadata` (JSONB), HNSW cosine index on `embedding` |
| `chat_conversations` | User conversations | `user_id` (FK), `created_at`, `updated_at`, composite index `(user_id, created_at DESC)` |
| `chat_messages` | Messages within conversations | `conversation_id` (FK), `role` (user/assistant), `content`, `citations` (JSON array), `created_at`, timestamps |
| `chat_quota_usage` | Per-user quota tracking | `user_id`, `month` (YYYY-MM), `queries_used`, composite PK `(user_id, month)` |

**Vector Storage:**
- Embedding model: Gemini `text-embedding-004` (768 dimensions, batched up to 100 texts/request)
- Index: HNSW on `kb_chunks.embedding` with cosine similarity
- Chunking: tiktoken-based (500-token windows, 50-token overlap), paragraph → sentence fallback
- Atomic ingestion: `KbIngestionService._replace_chunks()` deletes old chunks and inserts new ones per document (transactional)

**Sync Pipeline:**
- On numerology content CRUD (insert/update/delete): SQLAlchemy `after_insert/update/delete` mappers enqueue to asyncio worker queue
- Worker processes queue sequentially: embeds chunks, upserts to KB (`_process_one` in `kb_sync.py`)
- Atomic at session level: each job commits after successful embedding + chunk insert
- Listener registration gated on `GEMINI_API_KEY` presence (disabled in dev if key missing)

**Ingestion Services:**
| Service | Purpose |
|---------|---------|
| `EmbeddingService` | Gemini API client, retry logic (3× exponential backoff on retryable errors), batch processing |
| `Chunker` | Tiktoken-based text splitting, configurable max tokens (default 500) + overlap (default 50) |
| `KbIngestionService` | Atomic upsert/reindex/delete for documents, manages chunk lifecycle |
| `kb_sync` module | SQLAlchemy event listeners + asyncio worker queue, lifespan registration |

### 2b. Chat API (Chatbot RAG Core — Phase 02)

**Purpose:** User-facing RAG retrieval, LLM generation, and citation extraction for conversational numerology chatbot.

**Endpoints** (all under `/api/chat/conversations`):
| Method | Path | Auth | Status | Purpose |
|--------|------|------|--------|---------|
| POST | `/api/chat/conversations` | Required | 201 | Create new conversation (title optional) |
| GET | `/api/chat/conversations` | Required | 200 | List user's conversations (paginated) |
| GET | `/api/chat/conversations/{id}` | Required | 200/404 | Fetch conversation detail (ownership check) |
| DELETE | `/api/chat/conversations/{id}` | Required | 204 | Delete conversation (cascades messages) |
| GET | `/api/chat/conversations/{id}/messages` | Required | 200 | List messages in conversation |
| POST | `/api/chat/conversations/{id}/messages` | Required | 201 | Send user message → retrieve KB (or hybrid with PDF) → generate with LLM → return assistant reply + citations |

### 2c. User PDF Context (Chatbot RAG — Phase 03)

**Purpose:** Enable users to upload PDFs and attach them to conversations for hybrid KB + PDF retrieval.

**New Tables:**
| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `user_pdf_index` | PDF metadata + ownership | `user_id` (FK), `pdf_hash` (SHA-256), `filename`, `page_count`, `expires_at` (30d TTL), UNIQUE(user_id, pdf_hash), indexed `expires_at` for cleanup |
| `user_pdf_chunks` | Extracted text chunks + embeddings | `pdf_index_id` (FK), `page_number`, `content` (text), `embedding` (Vector(768)), HNSW cosine index, clustered on pdf_index_id |

**User PDF Storage & Lifecycle:**
- **Upload:** 25MB cap (streaming size check; nginx 26M for headroom), %PDF magic-bytes validation
- **Parsing:** pypdf extract + clean_text (normalize whitespace, hyphen repair)
- **Embedding:** Gemini text-embedding-004, same 768-dim vectors as KB
- **Attachment:** Conversation links via `chat_conversations.pdf_context_id` FK; ownership validated on PATCH
- **TTL:** 30d auto-expiry; re-upload slides TTL forward (active PDFs don't die)
- **Cleanup:** Nightly cron 03:00 UTC deletes expired UserPdfIndex + cascades chunks; temp uploads >1h swept

**Hybrid Retrieval (when pdf_context_id provided):**
- **Split budget:** Free tier top_k=3 splits as 2 PDF + 1 KB (PDF-favored when user attaches); paid tier configurable
- **Merge:** Top results sorted by similarity score; dedup by chunk_id
- **Citations:** PDF rows JOIN user_pdf_index.filename; citation shows "report.pdf/p4" not "user_pdf/4"
- **Fallback:** KB-only path preserved when no PDF attached (zero overhead Phase 02 compat)

**New Endpoints:**
| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| POST | `/api/chat/conversations/{id}/upload-pdf` | Required | Multipart file upload (25MB cap, auto-attach) |
| PATCH | `/api/chat/conversations/{id}/pdf-context` | Required | Attach/clear previously-uploaded PDF (ownership validated) |
| DELETE | `/api/chat/conversations/{id}/pdf-context` | Required | Clear PDF attachment (does not delete UserPdfIndex) |

**New Services:**
- **PdfMatchService:** SHA-256 hash + user-scoped lookup (finds existing PDF)
- **PdfParserService:** pypdf extract + clean_text helper
- **UserPdfService:** Orchestrate match-or-parse, atomic (user_id, pdf_hash) insert with race-condition recovery, TTL slide on re-upload

**New Config:**
```
USER_PDF_TTL_DAYS=30                      # PDF expiry window
USER_PDF_MAX_BYTES=26214400               # 25MB upload cap (26M in nginx config)
PDF_CHUNK_TOKEN_WINDOW=500                # Chunking (same as KB)
PDF_CHUNK_OVERLAP_TOKENS=50               # Overlap (same as KB)
```

**Backfill Script:** `scripts/backfill_pdf_hashes.py` — one-shot SHA-256 over user_reports.pdf_path (idempotent, skips missing files)

**Core Services:**
- **RetrievalService:** pgvector top-k cosine similarity (free tier: 3 chunks, threshold 0.6; paid tier configurable)
- **LlmService:** Gemini Flash/Pro wrapper with 30s timeout, streaming-ready handler, empty-response guard
- **PromptBuilder:** System prompt with anti-hallucination contract ("Tôi không có đủ thông tin để trả lời câu hỏi này." when KB insufficient), user message sanitization, chat history max 5 turns
- **CitationParser:** Regex-based [N] extraction from LLM text, bounds-check against chunk list, dedup + sort

**Anti-Hallucination Contract:**
- System prompt instructs LLM: "If provided excerpts are insufficient, respond with exactly 'Tôi không có đủ thông tin để trả lời câu hỏi này.'"
- Free tier hardcoded; Phase 05 adds paid tier quota switching
- Retrieval failure short-circuits to canonical phrase (no wasted LLM call)
- Empty/safety-blocked LLM response raises `LlmError` (not persisted as blank message)

**Config (app/config.py):**
```
RAG_TOP_K_FREE=3              # Chunks per query (free users)
RAG_TOP_K_PAID=8              # Chunks per query (paid users)
RAG_SIM_THRESHOLD=0.6         # Cosine similarity floor
HISTORY_MAX_MESSAGES=5        # Prior turns in prompt
LLM_TIMEOUT_SECONDS=30        # Gemini API call timeout
```

**Message Schema:**
- Request: `{"content": "string, 1-2000 chars"}`
- Response 201: `{"id": int, "role": "assistant", "content": string, "citations": [{"chunk_id": int, "document_id": int, "text": string}], "created_at": ISO8601}`
- Ownership enforced: users can only see/delete own conversations; other_user 404 (not 403)

### 2d. Streaming Chat Endpoint (Chatbot RAG — Phase 04)

**Purpose:** Server-Sent Events (SSE) endpoint for real-time chat message streaming, token-by-token delta delivery with citation extraction.

**New Endpoint:**
| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| POST | `/api/chat/conversations/{id}/messages/stream` | Required | Stream response as SSE (HTTP/1.1 keepalive required) |

**SSE Event Schema (Content-Type: text/event-stream):**
```
event: delta
data: {"token": "<text chunk>"}

event: delta
data: {"token": "...more tokens..."}

event: citations
data: {"citations": [{"index": 1, "chunk_id": 101, "document_id": 11,
       "source_type": "numerology:mission_number", "source_ref": "MN_1",
       "title": "T1", "score": 0.9}]}

event: done
data: {"message_id": 42, "input_tokens": 50, "output_tokens": 12,
       "model_used": "gemini-2.0-flash"}

event: error
data: {"code": "llm_error"|"internal_error", "message": "<str>"}
```

All JSON uses `ensure_ascii=False` — Vietnamese text preserved as-is in wire format.

**New Helper Modules:**
- **sse_formatter.py:** Single function `sse_event(event, data) -> bytes`, formats SSE frames
- **chat_turn.py:** Extracted shared logic (`persist_user_message`, `run_retrieval`, `build_turn_prompt`, `persist_assistant_message`) — used by both sync + stream endpoints to avoid duplication
- **_stream_generator.py:** Async generator `_event_gen()`, bridges sync LLM iterator to async SSE consumer via threading + queue

**Client→Server Flow:**
1. POST with `{"content": "...", "pdf_context_id": null/int}` (MessageIn accepts optional pdf_context_id override)
2. **Before generator starts:** Ownership check + user message persist (404/422 normal HTTP responses)
3. **Hardening gate (Phase 08):** `run_hardening_gates()` middleware checks abuse patterns, cost/quota budgets, feature flag status; blocks if violated (403/429)
4. **During stream:** Retrieval → LLM call → token-by-token delta events → citations event → done event
4. **On retrieval failure:** Emit single delta with `NO_INFO_VI` phrase, persist canonical assistant row, emit done (LLM not called)
5. **On mid-stream LLM error:** Emit `event: error` with `code: "llm_error"`. No broken assistant message committed (accumulation buffer never flushed if error before persist)

**Nginx SSE Configuration:**
Location regex matches `/api/chat/conversations/{id}/messages/stream`:
```nginx
location ~ ^/api/chat/conversations/\d+/messages/stream$ {
  proxy_pass http://api:8000;
  proxy_buffering off;
  proxy_request_buffering off;
  gzip off;
  proxy_read_timeout 300s;
  proxy_set_header X-Accel-Buffering no;
}
```

**Key Headers:**
- `X-Accel-Buffering: no` — disables nginx buffering
- `Cache-Control: no-cache`
- `Connection: keep-alive` (HTTP/1.1 persistent connection)

**LLM Service Changes:**
- **StreamResult dataclass:** Sidecar for token counts after stream exhausted
- **generate_stream() async method:** New streaming variant (separate from non-streaming `generate()`)
- **Bridge pattern:** Sync SDK iterator runs in `threading.Thread`; chunks pushed to `asyncio.Queue` via `loop.call_soon_threadsafe`; async consumer `await asyncio.wait_for(queue.get(), timeout)`
- **First-token timeout:** `self._timeout` applied only to first item; subsequent items have no per-token timeout (stream may have natural pauses)
- **Token counts:** Extracted from `usage_metadata` on last chunk, written to `result.input_tokens/output_tokens`

**Backend Files Created/Modified:**
| File | LOC | Action |
|------|-----|--------|
| `app/services/chat/sse_formatter.py` | 33 | created |
| `app/services/chat/chat_turn.py` | 97 | created (split from messages.py) |
| `app/services/chat/llm_service.py` | 222 | modified (+83 LOC: StreamResult + generate_stream) |
| `app/routers/chat/messages.py` | 222 | modified (rewritten: use chat_turn helpers + stream endpoint) |
| `app/routers/chat/_stream_generator.py` | 120 | created |

**Test Coverage:**
- 40 backend tests pass (13 new stream tests: happy-path, retrieval failure, LLM error, ownership/auth)
- Zero LOC violations: messages.py ≤220, _stream_generator.py ≤120, all ≤200 LOC targets met

**New Tables:**
| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `user_pdf_index` | PDF metadata + ownership | `user_id` (FK), `pdf_hash` (SHA-256), `filename`, `page_count`, `expires_at` (30d TTL), UNIQUE(user_id, pdf_hash), indexed `expires_at` for cleanup |
| `user_pdf_chunks` | Extracted text chunks + embeddings | `pdf_index_id` (FK), `page_number`, `content` (text), `embedding` (Vector(768)), HNSW cosine index, clustered on pdf_index_id |

**User PDF Storage & Lifecycle:**
- **Upload:** 25MB cap (streaming size check; nginx 26M for headroom), %PDF magic-bytes validation
- **Parsing:** pypdf extract + clean_text (normalize whitespace, hyphen repair)
- **Embedding:** Gemini text-embedding-004, same 768-dim vectors as KB
- **Attachment:** Conversation links via `chat_conversations.pdf_context_id` FK; ownership validated on PATCH
- **TTL:** 30d auto-expiry; re-upload slides TTL forward (active PDFs don't die)
- **Cleanup:** Nightly cron 03:00 UTC deletes expired UserPdfIndex + cascades chunks; temp uploads >1h swept

**Hybrid Retrieval (when pdf_context_id provided):**
- **Split budget:** Free tier top_k=3 splits as 2 PDF + 1 KB (PDF-favored when user attaches); paid tier configurable
- **Merge:** Top results sorted by similarity score; dedup by chunk_id
- **Citations:** PDF rows JOIN user_pdf_index.filename; citation shows "report.pdf/p4" not "user_pdf/4"
- **Fallback:** KB-only path preserved when no PDF attached (zero overhead Phase 02 compat)

**New Endpoints:**
| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| POST | `/api/chat/conversations/{id}/upload-pdf` | Required | Multipart file upload (25MB cap, auto-attach) |
| PATCH | `/api/chat/conversations/{id}/pdf-context` | Required | Attach/clear previously-uploaded PDF (ownership validated) |
| DELETE | `/api/chat/conversations/{id}/pdf-context` | Required | Clear PDF attachment (does not delete UserPdfIndex) |

**New Services:**
- **PdfMatchService:** SHA-256 hash + user-scoped lookup (finds existing PDF)
- **PdfParserService:** pypdf extract + clean_text helper
- **UserPdfService:** Orchestrate match-or-parse, atomic (user_id, pdf_hash) insert with race-condition recovery, TTL slide on re-upload

**New Config:**
```
USER_PDF_TTL_DAYS=30                      # PDF expiry window
USER_PDF_MAX_BYTES=26214400               # 25MB upload cap (26M in nginx config)
PDF_CHUNK_TOKEN_WINDOW=500                # Chunking (same as KB)
PDF_CHUNK_OVERLAP_TOKENS=50               # Overlap (same as KB)
```

**Backfill Script:** `scripts/backfill_pdf_hashes.py` — one-shot SHA-256 over user_reports.pdf_path (idempotent, skips missing files)

**Core Services:**
- **RetrievalService:** pgvector top-k cosine similarity (free tier: 3 chunks, threshold 0.6; paid tier configurable)
- **LlmService:** Gemini Flash/Pro wrapper with 30s timeout, streaming-ready handler, empty-response guard
- **PromptBuilder:** System prompt with anti-hallucination contract ("Tôi không có đủ thông tin để trả lời câu hỏi này." when KB insufficient), user message sanitization, chat history max 5 turns
- **CitationParser:** Regex-based [N] extraction from LLM text, bounds-check against chunk list, dedup + sort

**Anti-Hallucination Contract:**
- System prompt instructs LLM: "If provided excerpts are insufficient, respond with exactly 'Tôi không có đủ thông tin để trả lời câu hỏi này.'"
- Free tier hardcoded; Phase 05 adds paid tier quota switching
- Retrieval failure short-circuits to canonical phrase (no wasted LLM call)
- Empty/safety-blocked LLM response raises `LlmError` (not persisted as blank message)

**Config (app/config.py):**
```
RAG_TOP_K_FREE=3              # Chunks per query (free users)
RAG_TOP_K_PAID=8              # Chunks per query (paid users)
RAG_SIM_THRESHOLD=0.6         # Cosine similarity floor
HISTORY_MAX_MESSAGES=5        # Prior turns in prompt
LLM_TIMEOUT_SECONDS=30        # Gemini API call timeout
```

**Message Schema:**
- Request: `{"content": "string, 1-2000 chars"}`
- Response 201: `{"id": int, "role": "assistant", "content": string, "citations": [{"chunk_id": int, "document_id": int, "text": string}], "created_at": ISO8601}`
- Ownership enforced: users can only see/delete own conversations; other_user 404 (not 403)

### 2e. Chat Quota + Add-on Packages (Chatbot RAG — Phase 05)

**Purpose:** Monetize chat via per-message quota (free 3/day) + add-on packs (Flash/Pro, 30d). See Phase 05 changelog for full details.

### 2f. Chat Caching + Rate Limiting (Chatbot RAG — Phase 06)

**Purpose:** Optimize cost (semantic cache + Gemini prompt caching) and prevent abuse (two-bucket rate limiting on user + IP) with fail-closed semantics.

### 2g. Admin Chatbot Tuning (Chatbot RAG — Phase 07)

**Purpose:** Admin KB ingestion, prompt override with audit trail, conversation/analytics access, manual addon grants.

**Backend Complete — 10 New Endpoints (all under `/admin/chatbot`):**
- KB: POST `/kb/upload` (PDF/DOCX/TXT/MD, 25MB), GET `/kb/documents` (paginated), DELETE `/kb/documents/{id}`
- Prompt: GET/PUT/DELETE `/prompt` (override system prompt), GET `/prompt/history` (audit log)
- Conversation: GET `/conversations` (filter by user/tier/date), GET `/conversations/{id}` (detail)
- Analytics: GET `/analytics/overview?days=N` (query/user/response-time metrics)
- Addon: POST `/users/{user_id}/grant-addon` (manual grant, payment_id=NULL audit trail)

**Services:** `AdminKbService` (file extraction), `PromptSettingsService` (60s TTL cache + audit), `ChatAnalyticsService` (SQL aggregations).

**Hybrid Prompt (Deliberate Design):** In-code SYSTEM_PROMPT default + admin override via `chat_system_settings` table; `resolve_system_prompt()` centralizes fallback rule. Audit trail via `chat_system_settings_history` (append-only).

**Models (Alembic 0014):** `chat_system_settings` (key-value), `chat_system_settings_history` (audit log).

**Frontend Partial:** `/admin/chatbot` (dashboard), `/admin/chatbot/kb` (upload + list); deferred UI (prompt editor, conversation browser, analytics).

**Dependencies:** `python-docx>=1.1`

**New Tables (Alembic 0013):**
| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `semantic_cache_entries` | Cached responses for semantically-similar queries | `tier` (user tier scoped), `embedding` (Vector(768)), `answer` (text), `ttl_expires_at` (24h), HNSW cosine index |
| `rate_limit_buckets` | Token bucket counters (per-user + per-IP) | `user_id` or `ip_address` (unique scope), `bucket_type` (user\|ip), `tokens` (NUMERIC(10,2)), `daily_reset_date` (Asia/Bangkok), `daily_cap_refill_at` |
| `prompt_cache_handles` | Gemini cached_content resource names | `cache_key` (SHA-256), `gemini_cache_id` (resource name), `hit_count` (in-process counter), `expires_at` (1h TTL, refresh on hit), `created_at` |

**Pipeline (Atomic Order — Both Sync + Stream):**
1. Auth + user message persist (pre-commit)
2. Quota check (402 if exhausted)
3. **Rate limit check** (429 if buckets allow=false; two-bucket atomic: user + IP both evaluated, fail-closed on DB error)
4. Retrieval (KB + PDF hybrid)
5. **Semantic cache lookup** (cosine ≥0.92, tier-scoped, 24h TTL; NO_INFO_VI responses skipped)
6. **Prompt cache get_or_create** (SHA-256 cache_key, lazy threshold 5 hits, TTL 1h with refresh on hit, broad-strokes invalidation gated on KB content-hash short-circuit)
7. LLM call (with `cached_content=gemini_cache_id` if hit)
8. **Semantic cache insert** (fire-and-forget, own transaction post-commit, skips NO_INFO)
9. Persist assistant + quota decrement + commit
10. Return + cache hit response shape (stream: 40-char delta, done event: `from_cache=True`)

**SemanticCacheService:**
- `lookup(content, tier) -> answer|None` — pgvector cosine top-1, threshold 0.92
- `insert(content, answer, tier)` — fire-and-forget (own session, non-fatal)
- `cleanup_expired()` — nightly cron (part of `cleanup_semantic_cache` job, 03:15 UTC)

**RateLimitService:**
- `check_and_consume(user_id, ip, tier) -> RateLimitResult` — two-bucket SELECT FOR UPDATE (atomic)
  - User bucket: free 1 req/10s, pro 1 req/3s, daily 100/pro daily 1000 (reset Asia/Bangkok UTC+7 @ 07:00 local = UTC 00:00)
  - IP bucket: 5 cap/0.05s (50/day), stateless overflow
- **Fail-closed on DB error:** Any exception → `allowed=False, reason="rate_limit_unavailable"` (not fail-open as Phase 05 review flagged)
- Lock released before LLM call (single transaction commits rate-limit row immediately, then LLM outside lock)

**PromptCacheService:**
- `get_live_handle(cache_key) -> gemini_cache_id|None` — SELECT live handle, refresh TTL on hit
- `maybe_create(cache_key, prompt) -> gemini_cache_id|None` — lazy creation at 5 in-process hits (hit counter per cache_key)
  - Creates `CachedContent` via `client.caches.create()`; TTL 1h, auto-refreshes on hit
  - Race condition: concurrent threshold trips both call Gemini (second INSERT rolls back, orphan lifetime-expires)
- `invalidate_for_chunks_sync(sentinel_ids)` — broad-strokes DELETE all handles when KB content changes (gated by content-hash short-circuit in kb_ingestion_service to avoid spurious invalidation)
- `cleanup_expired()` — nightly delete TTL-expired rows (part of cleanup job)

**HTTP 429 Response (Rate Limited):**
```
HTTP/1.1 429 Too Many Requests
Retry-After: <ceil(retry_after_seconds)>
Content-Type: application/json

{
  "detail": {
    "code": "rate_limited",
    "retry_after": 7,
    "reason": "bucket_empty"|"daily_cap"|"ip_limit",
    "message": "Bạn gửi tin nhắn quá nhanh. Vui lòng đợi 7 giây."
  }
}
```

**Frontend (useRateLimitCountdown hook):**
- Countdown display on message input
- Disable send button during lockout
- Sonner toast variants: bucket_empty (warn, 3s), daily_cap (error, 8s)
- HTTP 429 handler with Retry-After parsing

**Background Job (cleanup_semantic_cache.py):**
- Runs nightly at 03:15 UTC
- Calls `SemanticCacheService.cleanup_expired()` + `PromptCacheService.cleanup_expired()`
- Separate sessions, one implicit transaction (all-or-nothing semantics for nightly cleanup)

**New Tables:**
| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `packages.package_kind` | Column added (enum: "pdf_download" \| "chat_addon") | Differentiates PDF subscriptions from message packs |
| `packages` | Extended columns | `message_count` (NULL for PDF), `tier` (Literal["flash", "pro"]), `validity_days` (30d ttl) |
| `chat_addon_purchases` | Track message pack sales | `user_id` (FK), `package_id` (FK), `addon_id` (PK = fulfilled addon), `payment_id` (idempotency key), `remaining_messages`, `expires_at` (now + validity_days), UNIQUE(user_id, payment_id) |

**Quota Resolution (Priority Order):**
1. **Active chat add-on:** If an unexpired `chat_addon_purchases` row exists with `remaining_messages > 0`, use it (SELECT FOR UPDATE, atomic decrement)
2. **Free tier (3/day):** If no active addon, check `chat_quota_usage` (month-based atomic counter via ON CONFLICT)
3. **402 Conflict:** If both are depleted, return HTTP 402 (Payment Required) with `detail.code = "quota_exceeded"`

**Key Services:**
- **QuotaService:** `check(user_id, decision) -> QuotaDecision` (type: "addon"|"free"|None), `decrement(user_id, decision)` (SELECT FOR UPDATE on addon, ON CONFLICT on free)
- **QuotaDecision dataclass:** Encodes decision type + addon_id (if addon used) + tier (if paid)
- **addon_fulfillment.fulfill_chat_addon():** Idempotent handler; checks `payment_id` uniqueness before INSERT

**Payment Integration:**
- `POST /api/chat/addons/{id}/purchase` → creates `UserPayment(status=1, content="CHATADDON{payment_id}")`
- SePay webhook matcher extended: branched on `payload.content`:
  - `NSQ-XXXXXXXX` → `Order` row → `fulfillment_service.fulfill_order`
  - `CHATADDON<id>` → `UserPayment` row → `approve_payment(payment_id)` (dispatcher branches on `package_kind`)
- `approve_payment()` calls `addon_fulfillment.fulfill_chat_addon()` if `package_kind='chat_addon'`

**Endpoints (New):**
| Method | Path | Auth | Status | Purpose |
|--------|------|------|--------|---------|
| GET | `/api/chat/addons` | Optional | 200 | List chat addon packages (all `package_kind='chat_addon'`) |
| POST | `/api/chat/addons/{id}/purchase` | Required | 201 | Initiate purchase, return bank account for transfer |
| GET | `/api/chat/quota` | Required | 200 | Get user's quota: `{free_remaining, addon_remaining, addon_expires_at, tier}` |

**SSE Quota Events (Stream Endpoint):**
- `quota_exceeded` (402 pre-check): quota depleted before streaming starts → error event with code
- `quota_exceeded_postcommit` (rare): quota check passed, but race condition between check + decrement (edge case, per spec risk table)

**Config (app/config.py):**
```
FREE_MESSAGES_PER_DAY=3      # Free tier daily limit (reset UTC)
ADDON_VALIDITY_DAYS=30       # Message pack expiry window
```

**Backend Files Created/Modified (Phase 05):**
| File | LOC | Action |
|---|---|---|
| `app/services/chat/quota_service.py` | 200 | created — QuotaService, QuotaDecision, QuotaConflictError |
| `app/services/chat/addon_fulfillment.py` | 88 | created — fulfill_chat_addon idempotent logic |
| `app/routers/chat/addons.py` | 97 | created — GET /api/chat/addons, POST .../purchase |
| `app/routers/chat/quota.py` | 42 | created — GET /api/chat/quota |
| `app/routers/chat/messages.py` | 212 | modified — quota gate + decrement in sync path |
| `app/routers/chat/_stream_generator.py` | 132 | modified — quota decrement in stream path (before commit) |
| `app/services/payment_service.py` | 100 | modified — branched approval on package_kind |
| `app/db/models/chat/chat_addon_purchase.py` | 30 | created |
| `app/schemas/chat/addon.py` | 35 | created — AddonPackageOut, QuotaOut |
| `alembic/versions/0012_chat_addons.py` | 50 | created — adds package_kind + message_count/tier/validity_days columns, chat_addon_purchases table |

**Code Review Fixes (all critical + selected high applied this phase):**
- **C1 — SePay webhook now matches `CHATADDON{payment_id}` content** → auto-fulfills chat addons via `approve_payment` dispatcher
- **C2 — Stream decrement moved BEFORE `db.commit()`** → single transaction with assistant message; closes revenue leak on client disconnect
- **C3 — `PackageCreate`/`PackageUpdate` Pydantic `model_validator`** rejects chat_addon with missing/invalid message_count, tier, validity_days
- **C4 — `.prettierrc.json` removed** (conflicted with existing team config)
- **H1+H4 — SSE `quota_exceeded_postcommit` error event** emitted when rare race drains addon between check and decrement
- **H2 — `onQuotaExceededRef` + `useCallback`** stabilizes callback identity across renders
- **H3 — Quota polling (10s, 5min cap)** with sonner toast on `/chat/upgrade` and inside `UpsellModal`
- **H5 — `PackageOut.field_validator`** coerces NULL `package_kind` to default

**Accepted / Deferred:**
- **H1 reserve-then-release** — not implemented; rare race can over-grant by 1 (free path) or trigger silent QuotaConflictError (addon path, now surfaced via SSE)
- **H6 — UTC date reset** for Asia/Bangkok users (07:00 local) — UI tooltip recommended in Phase 07
- **H7 — tier Literal case-sensitivity** — no active bug; admin form enforces lowercase

### 3. Nginx Reverse Proxy

**Config:** `deploy/nginx.conf` (116 lines)

**Tasks:**
- SSL termination (Certbot auto-renewal)
- HTTP→HTTPS redirect
- Gzip compression (text, JSON, HTML)
- Request forwarding to FastAPI (8000)
- Static file serving (`/static/*` + `/media/*`)
- WebSocket header pass-through (future-proof)
- Upload size limit: 20MB

**Locations:**
```
/               → proxy_pass http://api:8000
/media/         → alias /media/ (volume mount)
/static/        → alias /static/ (volume mount)
/.well-known/   → Certbot ACME validation
```

---

## Request Flows

### 1. Paid PDF Generation (Quota-Gated)

```
User (logged in)
    │
    ├─ GET /api/so-hoc?phone=0123456789&name=Nguyen%20Van%20A HTTP/1.1
    │  Authorization: Bearer eyJhbGc...
    │
    ▼ FastAPI auth middleware (get_current_user)
Validate JWT token
    ▼
Fetch user & profile (SELECT FOR UPDATE)
    ├─ Check quota > 0
    │  ├─ YES: proceed
    │  └─ NO: 403 Forbidden
    │
    ▼ Numerology calculation (calculate_numerology_numbers)
    ├─ Parse input (strip accents, normalize phone)
    ├─ Compute: so_chu_dao, so_nam_ca_nhan, so_khong_khat, etc. (9 types)
    ├─ Master number redirect (11→2, 22→4, 33→6)
    ├─ Fetch 22 numerology content tables from DB (by code + number)
    │
    ▼ Build Jinja2 context
    ├─ User data, calculated numbers, content HTML
    │
    ▼ Render invoice.html → HTML string
    │
    ▼ Render HTML → PDF (async wkhtmltopdf)
    │
    ▼ Decrement quota
    UPDATE user_profiles SET quota = quota - 1 WHERE user_id = X
    │
    ▼ Log download
    INSERT INTO user_downloads (user_id, type, created_at)
    │
    ▼ Return
    HTTP/1.1 200 OK
    Content-Type: application/pdf
    Content-Disposition: attachment; filename="so-hoc-DDMMYYYY.pdf"
    [PDF binary data]
```

### 2. Forgot / Reset Password (Email Link)

```
User (forgot-password page)
    │
    ├─ POST /auth/forgot-password { email }
    │
    ▼ FastAPI router
    Lookup user by email
    ├─ NOT FOUND or inactive: skip silently (no enumeration)
    └─ FOUND:
        UPDATE password_reset_tokens SET used_at=now()
          WHERE user_id=X AND used_at IS NULL   (invalidate prior tokens)
        INSERT raw token (SHA-256 hashed) — 30 min expiry
        send_password_reset_email(user.email, raw_token)
    │
    ▼ Always respond 202 Accepted
    │
    ─── (email contains)
    https://frontend/reset-password?token=<raw>

User opens link
    │
    ├─ POST /auth/reset-password { token, new_password }
    │
    ▼ consume_reset_token(): hash → lookup → check used_at + expires_at → mark used
    ▼ update_user_password(): bcrypt-hash + persist
    ▼ revoke_all_user_refresh_tokens(): forces re-login on all devices
    │
    ▼ 204 No Content
    │
    ✅ Frontend redirects to /login
```

### 3. Admin Content Edit

```
Admin (Next.js /admin/content/attitude-number/42)
    │
    ├─ Auth guard (useAdminAuth hook)
    │  └─ GET /auth/me (Bearer token)
    │     └─ Response: { is_superuser: true, ... }
    │
    ├─ GET /admin/content/attitude-number/42
    │
    ▼ FastAPI admin router
    Validate is_superuser (via get_current_superuser)
    │
    ▼ Fetch from DB
    SELECT * FROM attitude_number WHERE id = 42
    │
    ▼ Return Pydantic schema
    HTTP/1.1 200 OK
    { "id": 42, "code": 1, "title": "...", "content": "...", ... }
    │
    ├─ Admin submits form
    │  PUT /admin/content/attitude-number/42
    │  Content-Type: application/json
    │  { "title": "New Title", "content": "<p>New...</p>" }
    │
    ▼ FastAPI validate + update
    UPDATE attitude_number SET title='...', content='...' WHERE id=42
    │
    ✅ Changes live within 1s
```

---

## Data Flow Summary

```
┌─────────────────────────┐
│ Numerology Content (22) │ ← Admin UI edits via /admin/content/*
│ (PostgreSQL tables)     │
└────────────┬────────────┘
             │
             ├─ Paid calc: JOIN with numbers (→ PDF context)
             ├─ Free calc: JOIN with numbers (→ HTML preview)
             ├─ KB sync: after_insert/update/delete → embed → KB ingest
             └─ Cache candidates: Redis future (phase post-launch)

┌──────────────────────────────────┐
│ Knowledge Base & Chat            │ ← Populated by KB sync (Phase 01)
│ (kb_documents, kb_chunks,        │   kb_chunks.embedding (768-dim)
│  chat_conversations,             │   indexed HNSW cosine
│  chat_messages,                  │   Gemini embeddings (batched)
│  chat_quota_usage)               │
└──────────────────────────────────┘

┌─────────────────────────┐
│ User Data               │ ← OAuth/JWT login, profile updates
│ (users, user_profiles)  │
└────────────┬────────────┘
             │
             ├─ Quota decrement on paid PDF
             ├─ Download audit log (user_downloads)
             ├─ Chat quota (monthly queries)
             └─ Package assignment (user_packages)

┌─────────────────────────┐
│ Payment Tracking        │ ← Admin approval workflow
│ (user_payments)         │
└─────────────────────────┘

┌─────────────────────────┐
│ Static/Media Files      │ ← Image uploads, PDF storage
│ (Nginx volume mounts)   │
└─────────────────────────┘
```

---

## Key Integration Points

### Admin to API
- **Endpoint:** Backend provides `/admin/*` routes (auth protected, superuser-only)
- **Tech:** FastAPI HTTPException(403 Forbidden) if not superuser
- **Response Format:** `{data: {...}}` for objects, `{items: [...], total: N, limit: L, offset: O}` for lists

### Frontend to Auth
- **Endpoint:** `GET /auth/me` (Bearer token in Authorization header)
- **Response:** `{id, email, is_superuser, user_profile: {...}}`
- **Error:** HTTPException(401 Unauthorized) if token invalid

### External APIs
- **vietheart.net:** Async httpx call, ~2s timeout, failure non-fatal for paid endpoint
- **SMTP:** Outbound mail via standard `smtplib` (TLS optional). Empty `SMTP_HOST` falls back to log-only mode for local/dev.

---

## Error Handling

**Standard Response Shape:**
```json
{
  "detail": "Error message here"
}
```

**HTTP Status Codes:**
| Code | Case |
|------|------|
| 200 | Success |
| 201 | Created |
| 204 | No Content (logout, delete) |
| 400 | Validation error (bad input) |
| 401 | Unauthorized (missing/invalid token) |
| 403 | Forbidden (insufficient permissions) |
| 404 | Not found |
| 409 | Conflict (duplicate email on register) |
| 500 | Server error (bug) |
| 503 | Service unavailable (vietheart.net timeout) |

---

## Performance & Scaling

**Current:** Single VPS (2-4 vCPU), 4 Gunicorn workers

**Bottlenecks (known):**
- Numerology calc: ~100-200ms (DB joins for 22 tables)
- PDF render: ~3-5s (wkhtmltopdf CPU-bound)
- OAuth callback: ~500ms (token exchange)

**Future optimizations:**
- Redis cache for numerology content (read-heavy)
- Query optimization (index on frequently-filtered columns)
- CDN for static/media files
- Async PDF render queue (Celery future)

---

## Security Model

1. **JWT Tokens:** 15min access, 7day refresh
2. **Refresh Token Rotation:** Old token revoked on new refresh
3. **Password Hashing:** bcrypt via passlib
4. **HTTPS Only:** Nginx SSL termination, HSTS header
5. **CORS:** Frontend domain whitelist in FastAPI config
6. **Admin Protection:** is_superuser flag + endpoint guard
7. **SQL Injection:** SQLAlchemy parameterized queries
8. **File Upload:** MIME type + size validation, serve via Nginx (not app)

---

## Monitoring & Logging

**Currently:** Plain stdout (Docker logs)  
**Future (Phase post-launch):**
- Sentry for error tracking
- Prometheus + Grafana for metrics
- ELK/Loki for log aggregation

**Key Logs to Watch:**
- `app/routers/auth.py`: login failures, password reset flow
- `app/services/email_service.py`: `[email:stub]` lines mean SMTP not configured — wire real SMTP creds before launch
- `app/routers/numerology_paid.py`: quota exhaustion, PDF render failures
- `app/core/horoscope_client.py`: vietheart.net timeouts
