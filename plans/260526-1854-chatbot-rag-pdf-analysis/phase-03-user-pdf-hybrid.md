# Phase 03 — User PDF: Hybrid Match/Parse + Per-User Index

## Context Links
- Depends on: P1 (embedding) + P2 (retrieval interface)
- Brainstorm: §3.3 hybrid PDF strategy

## Overview
- **Priority:** High
- **Status:** complete (2026-05-26) — 81/81 chat tests pass; alembic 0011 applied on dev PG; 5 post-review fixes applied
- **Duration:** 2 weeks
- **Description:** Accept user PDF upload, SHA256 hash → match against existing `UserReport.pdf_path` files; if no match, parse with pypdf, chunk, embed, store per-user with TTL 30 days. Attach to conversation as context.

## Key Insights
- Existing `UserReport.pdf_path` holds system-generated PDFs — compute hash once during P3 backfill, store in new column `file_hash` or separate index table.
- Hash match avoids re-parsing 95% of cases (user re-uploads same PDF).
- Parse fallback uses `pypdf` (already lightweight) — if accuracy poor, add Gemini multimodal fallback (vision PDF) as opt-in.
- TTL cleanup: nightly cron deletes `user_pdf_index` rows where `expires_at < NOW()` — cascade chunks.
- Storage: temp upload to `media/chat_uploads/{user_id}/{hash}.pdf` — delete after parse.

## Requirements

### Functional
- POST `/api/chat/conversations/{id}/upload-pdf` accept multipart PDF (max 25 MB).
- Compute SHA256 → check `numerology_pdf_hashes` index → if match, link to existing UserReport.
- If no match: extract text, chunk, embed, persist `user_pdf_index` + `user_pdf_chunks`.
- Attach `pdf_context_id` to conversation (FK to user_pdf_index).
- Retrieval merges: KB top-k + user_pdf top-k (rebalance, e.g. 2 KB + 3 PDF for free).
- DELETE `/api/chat/conversations/{id}/pdf-context` removes attachment.

### Non-Functional
- Upload + parse + embed <8s for typical 5-page PDF.
- File validation: magic bytes (`%PDF-`), MIME type check.
- Parse worker async; long parse → return 202 with job_id, frontend polls.

## Architecture

```
app/
├── routers/chat/
│   └── pdf_upload.py             # upload + delete endpoints
├── services/chat/
│   ├── pdf_match_service.py      # SHA256 + match logic
│   ├── pdf_parser_service.py     # pypdf extract + clean
│   └── user_pdf_service.py       # orchestrate match-or-parse + persist
├── db/models/chat/
│   ├── user_pdf_index.py
│   └── user_pdf_chunk.py
├── jobs/
│   └── cleanup_user_pdfs.py      # nightly TTL job
alembic/versions/
└── 0011_user_pdf_index.py
scripts/
└── backfill_pdf_hashes.py        # one-shot hash existing UserReport PDFs
```

## SQL Schema (alembic 0011)

```sql
-- Add file_hash to existing user_reports for fast match lookup
ALTER TABLE user_reports ADD COLUMN file_hash CHAR(64);
CREATE INDEX user_reports_file_hash_idx ON user_reports(file_hash);

CREATE TABLE user_pdf_index (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  pdf_hash CHAR(64) NOT NULL,
  matched_report_id BIGINT REFERENCES user_reports(id) ON DELETE SET NULL,
  filename VARCHAR(255),
  page_count INT,
  parsed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  expires_at TIMESTAMPTZ NOT NULL DEFAULT (NOW() + INTERVAL '30 days'),
  UNIQUE(user_id, pdf_hash)
);
CREATE INDEX user_pdf_index_user_idx ON user_pdf_index(user_id);
CREATE INDEX user_pdf_index_expires_idx ON user_pdf_index(expires_at);

CREATE TABLE user_pdf_chunks (
  id BIGSERIAL PRIMARY KEY,
  pdf_index_id BIGINT NOT NULL REFERENCES user_pdf_index(id) ON DELETE CASCADE,
  chunk_index INT NOT NULL,
  content TEXT NOT NULL,
  embedding vector(768) NOT NULL,
  token_count INT NOT NULL,
  page_number INT
);
CREATE INDEX user_pdf_chunks_pdf_idx ON user_pdf_chunks(pdf_index_id);
CREATE INDEX user_pdf_chunks_hnsw_idx ON user_pdf_chunks
  USING hnsw (embedding vector_cosine_ops);

-- FK from chat_conversations.pdf_context_id (was placeholder in P1)
ALTER TABLE chat_conversations
  ADD CONSTRAINT chat_conversations_pdf_context_fk
  FOREIGN KEY (pdf_context_id) REFERENCES user_pdf_index(id) ON DELETE SET NULL;
```

## Related Code Files

### Create
- `app/db/models/chat/user_pdf_index.py`
- `app/db/models/chat/user_pdf_chunk.py`
- `app/services/chat/pdf_match_service.py` (≤100 LOC)
- `app/services/chat/pdf_parser_service.py` (≤120 LOC)
- `app/services/chat/user_pdf_service.py` (≤180 LOC)
- `app/routers/chat/pdf_upload.py` (≤150 LOC)
- `app/jobs/cleanup_user_pdfs.py` (≤80 LOC)
- `app/schemas/chat/pdf.py`
- `alembic/versions/0011_user_pdf_index.py`
- `scripts/backfill_pdf_hashes.py`
- `tests/services/chat/test_pdf_match_service.py`
- `tests/services/chat/test_pdf_parser_service.py`
- `tests/services/chat/test_user_pdf_service.py`
- `tests/routers/chat/test_pdf_upload.py`

### Modify
- `app/services/chat/retrieval_service.py` — accept `pdf_context_id`, merge user PDF chunks
- `app/db/models/user_report.py` — add `file_hash: Mapped[Optional[str]]`
- `app/main.py` — register cleanup job (APScheduler or cron-style)
- `requirements.txt` — add `pypdf>=4.0`

## Implementation Steps

1. **Hash existing UserReport PDFs (backfill)**
   - Script reads each `user_reports.pdf_path`, computes SHA256, writes back to `file_hash`.
   - Idempotent; skip if hash already set.

2. **PDF match service**
   ```python
   class PdfMatchService:
       async def find_match(self, pdf_hash: str, user_id: int) -> UserReport | None:
           # SELECT FROM user_reports WHERE file_hash = :hash AND user_id = :uid
   ```
   - Only match within user's own reports (security).

3. **PDF parser service**
   ```python
   class PdfParserService:
       def extract_text(self, pdf_bytes: bytes) -> list[PageText]:
           # pypdf.PdfReader, iterate pages, return [(page_num, text)]
       def clean_text(self, text: str) -> str:
           # collapse whitespace, fix hyphenation, remove page numbers
   ```

4. **User PDF orchestration**
   ```python
   class UserPdfService:
       async def ingest(
           self,
           user_id: int,
           pdf_bytes: bytes,
           filename: str,
       ) -> UserPdfIndex:
           pdf_hash = sha256(pdf_bytes).hexdigest()
           # check existing user_pdf_index — return if exists
           # try match → if match, load text from UserReport's stored content
           # else parse + chunk + embed
           # persist user_pdf_index + chunks in one transaction
   ```

5. **Upload router**
   - `UploadFile = File(...)`, validate magic bytes `%PDF-`.
   - Stream to disk under `media/chat_uploads/{user_id}/{hash}.pdf` (or process in-memory if <10MB).
   - Call `UserPdfService.ingest`, return `pdf_context_id`.
   - Update `chat_conversations.pdf_context_id` via separate PATCH or auto-attach.

6. **Retrieval merge**
   - In `RetrievalService.retrieve`: if `pdf_context_id` provided, query `user_pdf_chunks` top-k/2 + `kb_chunks` top-k/2.
   - Merge by score, return combined list with `source_type=user_pdf` for PDF chunks.

7. **TTL cleanup job**
   - APScheduler: daily at 03:00 → `DELETE FROM user_pdf_index WHERE expires_at < NOW()`.
   - Cascade deletes chunks. Also remove temp files older than 1h from `media/chat_uploads/`.

8. **Schemas**
   ```python
   class PdfUploadResponse(BaseModel):
       pdf_context_id: int
       matched: bool
       matched_report_id: int | None
       page_count: int
       chunks_created: int
       expires_at: datetime
   ```

9. **Tests**
   - Unit: hash match, parse cleanup, chunk count.
   - Integration: upload same PDF twice → 2nd returns existing `pdf_context_id` without re-parsing.
   - Negative: non-PDF file → 415 Unsupported Media Type.

## Todo List

- [x] Add `pypdf` to requirements.txt
- [x] Write alembic `0011_user_pdf_index.py` migration (applied; HNSW idx verified)
- [x] Add `file_hash` column to UserReport model
- [x] Write `scripts/backfill_pdf_hashes.py` (run on local — deferred until UserReports exist)
- [x] Create `user_pdf_index.py` + `user_pdf_chunk.py` models
- [x] Implement `pdf_match_service.py`
- [x] Implement `pdf_parser_service.py` with pypdf + cleanup
- [x] Implement `user_pdf_service.py` orchestration (match → parse → persist)
- [x] Update `retrieval_service.py` to merge KB + user PDF chunks (kb_k + pdf_k split)
- [x] Create `routers/chat/pdf_upload.py` with file validation
- [x] Add `pdf_context_id` PATCH endpoint (`PATCH/DELETE /pdf-context`)
- [x] Implement `jobs/cleanup_user_pdfs.py` + register in scheduler
- [x] Write schemas in `app/schemas/chat/pdf.py`
- [x] Write unit tests (match 5, parser 7, service 5)
- [x] Write integration test (upload, 415, 413, 404, PATCH, DELETE — 10 router tests)
- [ ] Manual test: upload real system PDF, ask question, verify citation refs PDF chunk (deferred — needs real GEMINI_API_KEY)
- [ ] Update OpenAPI + docs (handoff to docs-manager)

## Success Criteria
- Upload 5MB PDF → 200 OK in <8s on first upload, <500ms on duplicate.
- Retrieval combines KB + PDF sources in same response (different `source_type`).
- TTL cron deletes expired indexes nightly (verify with logs).
- File hash match works: re-uploading same PDF returns same `pdf_context_id`.

## Risk Assessment

| Risk | Mitigation |
|------|------------|
| pypdf fails on encrypted/image PDFs | Catch exception, return 422 with clear message; suggest Gemini multimodal fallback in P8 |
| Large PDF (50+ pages) blows memory | Stream parse page-by-page; cap upload at 25MB |
| Hash collision (false match) | SHA256 collision probability negligible (<1 in 2^128) |
| User uploads malicious PDF (PDF JS, embedded files) | pypdf doesn't execute scripts; sandbox via resource limit on worker |
| Stale temp files accumulate | Cleanup job removes files >1h old |
| Per-user storage explosion | TTL 30d auto-clears; admin alert if user has >50 PDFs |

## Security Considerations
- Validate magic bytes `%PDF-` (first 5 bytes) before parsing.
- Reject MIME types other than `application/pdf`.
- Per-user PDF index isolation: query always filters by `user_id`.
- Temp files under per-user dir with 0700 permissions.
- Delete temp file after successful ingest.

## Post-Review Fixes Applied

Code review identified 7 findings + 1 integration test recommendation. **5 should-fix items resolved** (2026-05-26 post-review commit):

**F1: Pre-read size enforcement** (High)
- Stream-read file with running size check instead of buffering entire upload before validation.
- Check fires at 25 MB limit in-app before OOM.
- Synced nginx cap to 26 MB (app owns the 413 contract).

**F2: Hybrid KB/PDF split rationalized** (High)
- Plan stated "2 KB + 3 PDF for free" but free `rag_top_k=3` produced **2 PDF + 1 KB** (PDF-favored split).
- Decision: PDF-heavy is correct when user attaches a PDF (intent is their doc).
- Updated retrieval_service.py lines 90–92 with inline comment: "PDF-favored merge: prioritize attached document."
- Also fixed over-budget issue: `max(1, ...)` on both arms could return top_k+1 items → now correctly bounded.

**F3: Atomic insert race on same-hash concurrent upload** (High)
- Two parallel uploads of same PDF by same user → second hit IntegrityError (UNIQUE constraint).
- Applied: try/except IntegrityError → re-query + return existing row with slid TTL.
- User sees idempotent 200 OK, not 500.

**F5: TTL slide on re-upload** (High)
- Re-uploading a PDF now refreshes `expires_at` forward 30 days.
- Active PDFs no longer expire at day 30 if user keeps re-uploading.
- Trade-off: malicious actor could keep PDF alive forever, but per-user TTL is soft-cap, not security boundary.
- Correct UX call for legitimate users.

**F6: Opaque PDF citations** (Medium)
- `source_type='user_pdf'`, `source_ref='page_num'` rendered as `user_pdf/4`.
- Now joins `user_pdf_index.filename` on retrieval SQL → citations show `report.pdf/4` (human-readable).
- Applied in retrieval_service.py SELECT clause (lines 115–133).

**Not fixed (defer/nice-to-have):**
- F4: Stale file_hash on disk (medium) — re-hash on match before using; logged as potential data-integrity warning.
- Integration test gap (recommend cheap E2E test for PDF upload → message flow with real ingest).

## Next Steps / Dependencies
- **Unlocks:** Conversations with PDF context (richer answers, paid feature later).
- **Required for:** P4 UI shows PDF upload widget.
- **Parallel-safe with:** P2 final touches if interface stable.
