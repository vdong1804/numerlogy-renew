# Phase 03 Sync Report — User PDF + Hybrid Retrieval (Complete)

**Date:** 2026-05-27  
**Review:** code-review-260526-2147-phase-03-pdf.md (7.5/10 overall)  
**Status:** ✓ COMPLETE (code-complete + 5 should-fix items applied)

---

## What Landed

**7 new files (634 LOC code + tests):**
- Models: `user_pdf_index.py`, `user_pdf_chunk.py`
- Services: `pdf_match_service.py`, `pdf_parser_service.py`, `user_pdf_service.py`
- Router: `pdf_upload.py` (upload + PATCH/DELETE endpoints)
- Jobs: `cleanup_user_pdfs.py` (nightly TTL cleanup at 03:00)
- Schemas: `pdf.py`

**5 new endpoints:**
- `POST /api/chat/conversations/{id}/upload-pdf` — accept multipart PDF (≤25 MB)
- `PATCH /api/chat/conversations/{id}/pdf-context` — attach to conversation
- `DELETE /api/chat/conversations/{id}/pdf-context` — detach
- Implicit hybrid retrieval merge when `pdf_context_id` provided

**Database:**
- Alembic 0011 applied on dev PG (pgvector image required from P1, not yet staged)
- New tables: `user_pdf_index` (TTL 30d, UNIQUE(user_id, pdf_hash)), `user_pdf_chunks` (Vector(768) + HNSW)
- User_reports: added `file_hash` column for fast match lookup
- Chat_conversations: `pdf_context_id` FK constraint to user_pdf_index

**Hybrid retrieval logic:**
- When `pdf_context_id` given, split top_k: **2 PDF + 1 KB for free tier** (top_k=3)
- Merge by score, return combined list with `source_type=user_pdf` for PDF chunks
- KB-only path (no PDF) has zero overhead

**Tests:**
- 27 new tests (5 match + 7 parser + 6 service + 2 retrieval hybrid + 10 router)
- All 82/82 chat tests pass

---

## Post-Review Fixes Applied (2026-05-26)

Code review flagged 7 high/medium + 4 low-priority items. **5 should-fix resolved:**

| # | Finding | Fix |
|---|---------|-----|
| F1 | Pre-read size DoS — file.read() buffers entire upload before 413 check | Stream-read with running size check; synced nginx cap to 26 MB |
| F2 | KB/PDF split inverted vs plan — plan said "2 KB + 3 PDF" but got "2 PDF + 1 KB" | Decision: PDF-favored is correct (user's doc is intent); documented inline comment |
| F3 | Concurrent same-hash upload race → IntegrityError 500 | try/except IntegrityError → re-query + return existing with slid TTL |
| F5 | TTL not refreshed on re-upload — active PDFs expire at day 30 anyway | expires_at slides forward on re-upload; correct UX for legitimate users |
| F6 | Opaque PDF citations render as "user_pdf/4" | Join filename from user_pdf_index → shows "report.pdf/4" |

**Not fixed (defer):**
- F4: Stale file_hash on disk (re-verify before using; medium priority, low likelihood in immutable design)
- Integration test gap: E2E PDF upload → message flow (recommend cheap addition, not blocking)

---

## Current Progress

| Phase | Status | Notes |
|-------|--------|-------|
| P1: Foundation | ✓ Complete | DB schema, embedding service, KB ingest |
| P2: Core Chat | ✓ Complete | Retrieval, non-streaming, citations |
| P3: User PDF | ✓ Complete | Upload, match, parse, hybrid merge |
| P4: Streaming UI | ⏳ Pending | SSE + Next.js /chat page |
| P5: Quota + Add-ons | ⏳ Pending | Daily reset, addon packages, payment |
| P6: Cache + Rate Limit | ⏳ Pending | Semantic cache, token bucket |
| P7: Admin Tuning | ⏳ Pending | KB upload UI, prompt editor, analytics |
| P8: Hardening + Launch | ⏳ Pending | Cost monitor, abuse detection |

**Progress: 3/8 phases complete (37.5%)**

---

## Phase 04 Readiness

**Dependency: P3 → P4 is unblocked.**

P4 (Streaming UI) depends on:
- ✓ Hybrid retrieval endpoint (retrieval_service.py already handles pdf_context_id)
- ✓ PDF upload endpoint (ready)
- ✓ Chat conversation endpoints (P2)

**Ready to start:** P4 can proceed immediately. Frontend PDF upload widget + SSE integration can build on current API surface.

**Cross-references in P4 file:** References "Phase 03 hybrid retrieval" but no implementation dependencies. P4 assumes `/api/chat/retrieve` and `/api/chat/conversations/{id}/upload-pdf` exist (both ✓ done).

---

## Data Integrity Notes

- Per-user isolation: belt-and-suspenders (user_id in match query, insert, PATCH ownership, retrieval scope)
- File hash match: SHA256 collision negligible; re-upload idempotent
- TTL cleanup: 03:00 cron + edge case where cleanup runs during upload (row deleted → 500 on first message) is accepted risk; rare since expired rows are >30d old, new inserts default to NOW() + 30d
- Temp file cleanup: dead code in cleanup_user_pdfs.py (`_sweep_temp_uploads`) since in-memory upload path used; status quo acceptable (KISS)

---

## Unresolved Questions

1. **pgvector extension deployment:** P1 plan defers staging `CREATE EXTENSION vector` to prod until "close to launch." Phase 03 migration (Alembic 0011) is written but not runnable on prod PG without pgvector. When should pgvector be provisioned — before P4 UI, or closer to P8?

2. **Optional backfill strategy for existing UserReport PDFs:** Backfill script (scripts/backfill_pdf_hashes.py) reads each UserReport PDF from disk, hashes, writes file_hash. Idempotent but wasteful on re-runs if files are missing. Should we tag missing files with sentinel value or column, or leave as-is (current behavior: skip, re-process next run)?

3. **File-on-disk freshness guarantee:** If a UserReport PDF file is regenerated or edited on disk without updating file_hash column, retrieval would parse stale bytes. Current design assumes UserReports are immutable. Should we add a re-hash guard before parsing matched files, or document immutability invariant?

4. **Integration test coverage:** Code review recommends cheap E2E test (PDF upload → message with real ingest, no Gemini key). Should this be added to P3 todo before closing, or deferred to P4 (UI testing)?

5. **Manual hallucination test (plan todo line 207):** When is the gate for running it? Before P4 UI merge, or gated to pre-production deploy (P8)?
