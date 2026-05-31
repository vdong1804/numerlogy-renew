# Phase 07 — Admin Tuning: KB Upload + Prompt Editor + Analytics

## Context Links
- Depends on: P1 (KB ingestion), P5 (addon packages), P6 (cache stats)
- Brainstorm: §4.4 admin UI scope

## Overview
- **Priority:** Medium-High
- **Status:** complete (code 2026-05-28; manual QA + runbook doc pending)
- **Duration:** 1 week
- **Description:** Admin UI for uploading external KB docs (PDF/Word), editing system prompt, viewing conversations, dashboard with cost + cache hit rate + abuse flags.

## Key Insights
- Reuse existing admin auth (superuser check from `User.is_superuser`).
- KB upload reuses P1 `kb_ingestion_service` — admin path adds `source_type='admin_upload'`.
- Prompt editor: single template stored in DB (`system_settings.chat_system_prompt`) — versioned.
- Conversation viewer: filter by user, date, tier; show full thread + citations for audit.
- Analytics: read-only Postgres queries — no separate analytics DB needed at this scale.

## Requirements

### Functional
- POST `/api/admin/chatbot/kb/upload` — admin uploads PDF/DOCX/TXT → ingested as KB doc.
- GET/DELETE `/api/admin/chatbot/kb/documents` — list + delete admin docs.
- GET/PUT `/api/admin/chatbot/prompt` — read/update system prompt template.
- GET `/api/admin/chatbot/conversations` — paginated list with filters.
- GET `/api/admin/chatbot/conversations/{id}` — full thread + citations.
- GET `/api/admin/chatbot/analytics/overview` — daily messages, cache hits, cost, top questions, flag rate.
- POST `/api/admin/chatbot/users/{id}/grant-addon` — manual addon grant (refunds, comp).

### Non-Functional
- Admin endpoints require `User.is_superuser`.
- Analytics query <2s for 30-day window.
- KB upload accepts up to 100 MB.

## Architecture

```
app/
├── routers/admin/
│   └── chatbot.py                      # all admin chatbot routes
├── services/chat/
│   ├── admin_kb_service.py             # PDF/DOCX extract + ingest
│   ├── prompt_settings_service.py      # CRUD system prompt
│   └── chat_analytics_service.py       # SQL aggregations
├── db/models/chat/
│   └── system_settings.py              # generic key-value (or chat-specific)
alembic/versions/
└── 0014_admin_settings.py
```

### Frontend (Admin)
```
Numerology-Landing-Page/src/pages/admin/chatbot/
├── index.tsx                # dashboard
├── kb.tsx                   # KB document manager
├── prompt.tsx               # prompt editor
├── conversations.tsx        # conversation browser
└── analytics.tsx            # charts + tables

src/modules/admin/chatbot/
├── KbDocumentList.tsx
├── KbUploadForm.tsx
├── PromptEditor.tsx
├── ConversationViewer.tsx
└── AnalyticsCharts.tsx
```

## SQL Schema (alembic 0014)

```sql
CREATE TABLE chat_system_settings (
  id BIGSERIAL PRIMARY KEY,
  key VARCHAR(100) NOT NULL UNIQUE,
  value TEXT NOT NULL,
  updated_by BIGINT REFERENCES users(id) ON DELETE SET NULL,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  version INT NOT NULL DEFAULT 1
);

-- History of prompt changes (audit)
CREATE TABLE chat_system_settings_history (
  id BIGSERIAL PRIMARY KEY,
  key VARCHAR(100) NOT NULL,
  value TEXT NOT NULL,
  changed_by BIGINT REFERENCES users(id) ON DELETE SET NULL,
  changed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

## Related Code Files

### Create (backend)
- `app/routers/admin/chatbot.py` (≤200 LOC)
- `app/services/chat/admin_kb_service.py` (≤120 LOC) — extract PDF/DOCX
- `app/services/chat/prompt_settings_service.py` (≤80 LOC)
- `app/services/chat/chat_analytics_service.py` (≤180 LOC)
- `app/db/models/chat/system_settings.py` (≤60 LOC)
- `app/schemas/chat/admin.py`
- `alembic/versions/0014_admin_settings.py`
- `tests/routers/admin/test_chatbot_admin.py`
- `tests/services/chat/test_admin_kb_service.py`
- `tests/services/chat/test_chat_analytics_service.py`

### Create (frontend) — listed above

### Modify
- `app/services/chat/prompt_builder.py` — load system prompt from `prompt_settings_service` instead of constant
- `app/services/chat/admin_kb_service.py` — call `kb_ingestion_service.upsert_document(source_type='admin_upload', ...)`
- `requirements.txt` — add `python-docx>=1.1` for Word files
- Admin nav (existing): add "Chatbot" section

## Implementation Steps

1. **Schema**
   - Alembic 0014: settings table + history.
   - Seed default system prompt row (from Phase 02 hardcoded version).

2. **Settings service**
   ```python
   class PromptSettingsService:
       async def get_active() -> str  # 'chat_system_prompt' key
       async def update(new_value: str, updated_by: int)
           # snapshot old to history, bump version
   ```
   - Cache in-process with 60s TTL to avoid hot reads.

3. **Update prompt_builder**
   - Replace constant `SYSTEM_PROMPT = "..."` with `await prompt_settings.get_active()`.
   - Invalidate prompt cache (P6) when version changes.

4. **Admin KB service**
   ```python
   class AdminKbService:
       def extract_pdf(bytes) -> str  # pypdf
       def extract_docx(bytes) -> str  # python-docx
       def extract_txt(bytes) -> str
       async def ingest_upload(filename, file_bytes, admin_id) -> KbDocument
   ```
   - Detect MIME, extract, pass to `kb_ingestion_service.upsert_document`.

5. **Analytics service**
   ```python
   class ChatAnalyticsService:
       async def overview(start_date, end_date) -> dict:
           # daily message count by tier
           # cache hit rate
           # avg latency
           # top 20 questions (by content cluster — simple GROUP BY content for MVP)
           # cost estimate: sum(input_tokens * price + output_tokens * price)
           # users hitting rate limit count
           # quota-exhausted-then-purchased conversion
   ```
   - Pure SQL queries, no LLM calls.

6. **Admin router**
   - `/api/admin/chatbot/...` — all routes `Depends(get_superuser)`.
   - KB upload: multipart, validate type, call `admin_kb_service`.
   - Conversations browser: filters via query params (user_id, date_from, date_to, tier).
   - Manual addon grant: insert `ChatAddonPurchase` with `payment_id=NULL`, log to audit.

7. **Frontend admin pages**
   - Reuse existing admin layout (`src/layouts/admin` or similar).
   - `index.tsx`: dashboard with cards (today's msgs, cache rate, cost, abuse flags).
   - `kb.tsx`: table of KB documents (source_type, title, chunks, updated_at) + upload drag-drop.
   - `prompt.tsx`: textarea + version history + save with confirm.
   - `conversations.tsx`: searchable table → click row → modal with full thread + citations.
   - `analytics.tsx`: Recharts line/bar charts (daily messages, cost trend, cache hit %).

8. **Backups**
   - Document `chat_system_settings_history` retention — keep forever (small table).

9. **Tests**
   - Admin KB upload: PDF, DOCX, TXT each ingested correctly.
   - Non-superuser hits admin endpoint → 403.
   - Prompt update: history row created, version bumped.
   - Analytics: seed 50 messages, verify counts match.

## Todo List

- [x] Alembic 0014 migration with settings + history tables
- [x] Seed default system prompt row
- [x] Implement `system_settings.py` model
- [x] Implement `prompt_settings_service.py` with in-memory cache + invalidation
- [x] Update `prompt_builder.py` to load from DB (hybrid: in-code default + DB override)
- [x] Add `python-docx` to requirements
- [x] Implement `admin_kb_service.py` (PDF/DOCX/TXT extract)
- [x] Implement `chat_analytics_service.py` SQL aggregations
- [x] Create `routers/admin/chatbot.py` with all endpoints
- [x] Wire superuser dependency
- [x] Build admin Next.js pages (5 pages: index, kb, prompt, conversations, analytics)
- [x] Build admin components (KbDocumentList, KbUploadForm, PromptEditor, ConversationViewer, AnalyticsCharts)
- [x] Hook KB sync (P1) to invalidate prompt cache on KB change — already done in Phase 01
- [x] Write tests (admin endpoints, analytics queries) — 36 tests, all pass
- [ ] Manual QA: admin uploads PDF → ingested → chatbot answers using new content
- [ ] Document admin runbook in `docs/admin-chatbot-runbook.md`

## Post-Implementation Notes (2026-05-28)

### Backend Implementation Complete
- **Alembic 0014:** `chat_system_settings` + `chat_system_settings_history` tables deployed.
- **Models:** `ChatSystemSetting` + `ChatSystemSettingHistory` ORM models in `app/db/models/chat/system_settings.py`.
- **Services:**
  - `prompt_settings_service.py`: get/update/delete/list_history with 60s in-process TTL cache + audit log.
  - `admin_kb_service.py`: PDF/DOCX/TXT/MD extraction + ingest via `KbIngestionService` (source_type='admin_upload').
  - `chat_analytics_service.py`: SQL aggregations (daily messages, top questions, cost by model, cache stats, addon purchases).
- **Router:** `app/routers/admin/chatbot.py` — all 7 endpoints (KB upload/list/delete, prompt GET/PUT/DELETE/history, conversations list+detail, analytics, addon grant).
- **Schemas:** Pydantic schemas in `app/schemas/chat/admin.py`.
- **Dependencies:** `python-docx>=1.1` added to pyproject.toml.
- **Tests:** 28 tests across 4 test files, all pass (215 total suite, 4 skipped, 0 failures).

### Key Design Deviation: Hybrid Prompt Strategy
Per user decision, prompt is NOT fully DB-driven:
- **Default:** In-code `SYSTEM_PROMPT` constant (enables Gemini explicit cache stable path).
- **Override:** DB row in `chat_system_settings` overrides when set + versioned.
- **Resolver:** `prompt_builder.resolve_system_prompt()` checks DB first, falls back to constant.
- **Impact:** Keeps cost-optimized cache in common case; allows admin tuning without code deploy.

### Frontend Implementation Complete (5/5 Pages, 5/5 Components)
- **Pages:** `pages/admin/chatbot/{index,kb,prompt,conversations,analytics}.tsx`.
- **Components:** `kb-upload-form.tsx`, `kb-document-list.tsx`, `prompt-editor.tsx`,
  `conversation-viewer.tsx`, `analytics-charts.tsx` (DailyMessagesChart + CostByModelChart).
- **Nav:** "Chatbot RAG" group in `admin-nav-config.ts` exposes all 5 entries.
- **Charts:** recharts BarChart (vertical + horizontal layouts) reused from existing dashboard pattern.
- **Filters:** Conversations browser supports user_id / tier / date_from / date_to query params; analytics page has 7/14/30/60/90-day window selector.

### Code Review Applied (260528-1325)
- **H1 (High):** Upload limit 100MB → 25MB (DoS guard). ✓ Fixed.
- **H3 (High):** History `changed_by` now = user making change (not prior author); `delete()` accepts `deleted_by` param. ✓ Fixed.
- **M4 (Medium):** Semantic cache hit-rate denominator = `hits + assistant_messages` (not `hits + total_messages`). ✓ Fixed.
- **Code Quality Score:** 7.8/10. H2 (repo-wide `get_db` auto-commit) and M3 (analytics timezone-naive on PG) deferred.

### Remaining Items (Out of Code Scope)
- Manual QA: admin PDF upload → ingestion → chatbot response verification (requires real Gemini key + running stack).
- Admin runbook documentation (`docs/admin-chatbot-runbook.md`) — deferred to follow-up docs pass.

## Success Criteria
- Admin uploads PDF → KB doc + chunks visible in admin table within 30s.
- Editing system prompt + save → next chat uses new prompt (verify with curl).
- Conversation browser shows last 100 conversations with filters.
- Analytics dashboard renders in <3s for 30-day window.
- Non-superuser receives 403 on every admin endpoint.

## Risk Assessment

| Risk | Mitigation |
|------|------------|
| Admin uploads garbage PDF | Validate page count, text length min; reject empty |
| Prompt edit breaks chatbot | Show "test prompt" button before save; preserve prev version |
| Analytics query slow | Add indexes on `chat_messages(created_at, tier)`; pre-aggregate in P8 if needed |
| Manual addon grant abused | Audit log; require notes field; surface in admin daily report |
| Conversation viewer exposes user PII | Redact email/phone in display by default; toggle to reveal with audit |

## Security Considerations
- All admin routes `Depends(get_superuser)` — strict check.
- Audit log every admin action (settings change, addon grant, doc delete).
- KB file uploads sanitized (no executable types).
- Conversation viewer: hide content older than 90d by default (privacy).

## Next Steps / Dependencies
- **Unlocks:** Self-service KB updates without code deploy.
- **Required for:** Sustainable operations post-launch.
- **Parallel-safe with:** P6 (different concerns), P8 final hardening.
