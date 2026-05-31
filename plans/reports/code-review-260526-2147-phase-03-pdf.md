# Code Review — Phase 03: User PDF + Hybrid Retrieval

**Date:** 2026-05-26 22:47
**Scope:** 11 new files + 3 modified (LOC: 634 in 6 reviewed code files, +tests/migration)
**Tests:** 81/81 chat suite pass; full 257/271 (14 unrelated)
**Bar:** P1=7.5, P2=7.5

## Overall Score: 7.5/10

Clean architecture, good per-user isolation, sensible idempotency. Two genuine
defense-in-depth gaps (pre-read size + atomic insert race) and one inverted
budget vs plan. Implementation is leaner than the LOC budget across the board.

---

## Critical Issues (blocking)

**None.** No data leak, no auth bypass, no broken constraint. The two security
items below are defense-in-depth, not exploitable in the current deploy (nginx
caps body at 20MB *upstream* — see #1).

---

## High Priority

### 1. Pre-read size enforcement — `pdf_upload.py:68-69`

```python
data = await file.read()         # reads ENTIRE body into RAM first
_validate_pdf_bytes(data)        # checks size AFTER
```

`file.read()` materializes the whole upload before the 25MB check fires. An
attacker streaming 1GB hits OOM before the 413 ever returns.

**Mitigation today:** nginx `client_max_body_size 20M` (deploy/nginx.conf:40)
truncates earlier, so prod is safe-ish — but:

- 20MB nginx cap < 25MB app cap → **inconsistent limits**; uploads between
  20–25MB silently fail at the proxy with a 413 nginx error page (not the JSON
  envelope the app returns).
- Dev/local without nginx has no protection.

**Fix (should-fix):** stream-read with running size check:

```python
MAX = 25 * 1024 * 1024
buf = bytearray()
async for chunk in file.stream():           # or iterate in 1MB reads
    buf.extend(chunk)
    if len(buf) > MAX:
        raise HTTPException(413, "...")
data = bytes(buf)
```

Also: bring nginx cap to 26M (slight headroom > app cap) so the app owns the
413 contract.

### 2. Inverted KB/PDF budget split — `retrieval_service.py:91-92`

```python
pdf_k = max(1, (top_k + 1) // 2)   # top_k=3 → pdf_k=2
kb_k  = max(1, top_k - pdf_k)      # top_k=3 → kb_k=1
```

Plan §Requirements (line 27) says **"2 KB + 3 PDF for free"** but free tier
`rag_top_k_free` is 3, so this gives **2 PDF + 1 KB**. The split favors PDF —
which is probably the right call when a user attaches a PDF (their doc is the
intent), but it does **not match the plan's stated example**.

**Decide & document one way:**
- If current behavior is intentional (PDF-heavy when attached) → update plan
  text and add a comment on lines 90-92.
- If plan is the source of truth → flip: `kb_k = (top_k + 1) // 2`.

Also: `max(1, …)` for both arms means **top_k=2 returns up to 2+1=3 chunks**
(over-budget). Final `merged[:top_k]` truncates, but you've still paid for one
extra DB roundtrip / embedding-distance compute per query.

### 3. Atomic insert race for same hash same user — `user_pdf_service.py:69-97`

Flow: `_find_existing_index` → (gap) → `INSERT user_pdf_index`. Two parallel
uploads of the same PDF by the same user:

- T1: SELECT → none
- T2: SELECT → none
- T1: INSERT → ok
- T2: INSERT → `IntegrityError` (uq_user_pdf_index_user_hash) → 500

UNIQUE constraint protects DB integrity; user gets a generic 500.

**Fix (should-fix):** wrap the insert + flush in `try/except IntegrityError`,
re-query, return the existing row:

```python
try:
    self.session.add(pdf_index)
    await self.session.flush()
except IntegrityError:
    await self.session.rollback()      # or savepoint
    existing = await self._find_existing_index(user_id, pdf_hash)
    return PdfIngestResult(pdf_index=existing, ..., reused_existing=True)
```

Or use PG-specific `INSERT … ON CONFLICT (user_id, pdf_hash) DO NOTHING
RETURNING *`. The savepoint approach is portable to sqlite tests.

### 4. Stale-hash trust on matched_report.pdf_path — `user_pdf_service.py:83-87`

```python
if matched_report and matched_report.pdf_path and os.path.exists(...):
    with open(matched_report.pdf_path, "rb") as f:
        pages = self.parser.extract_pages(f.read())
```

We trust the hash in `user_reports.file_hash` matches the file on disk. The
backfill computes it once; if the file is later regenerated/edited without
updating `file_hash`, we'd parse different content than the user uploaded.

**Likelihood:** low — user reports are immutable in current design (P3 plan
implies "system-generated PDFs"). But there's no DB trigger or write-time hook
that enforces the invariant.

**Fix (nice-to-have):** re-hash file on disk and confirm match before using it
(defeats the optimization if done unconditionally — better: log warn + fall
back to uploaded bytes on mismatch). Cheap 1-line guard:

```python
if _sha256_file(matched_report.pdf_path) != pdf_hash:
    logger.warning("stale file_hash on UserReport %d", matched_report.id)
    pages = self.parser.extract_pages(pdf_bytes)
```

### 5. TTL not refreshed on re-upload — `user_pdf_service.py:69-77`

Re-upload returns existing row, `expires_at` unchanged. A user who actively
uses a PDF 29 days in still loses it on day 30.

**Fix (should-fix):** slide on re-use:

```python
if existing is not None:
    existing.expires_at = _default_expires_at()
    await self.session.flush()
    return PdfIngestResult(..., reused_existing=True)
```

Trade-off: a malicious actor could keep a PDF alive forever by re-uploading,
but per-user TTL was a soft-resource cap, not a security boundary. Slide is the
right UX call.

---

## Medium Priority

### 6. Opaque PDF citations — `retrieval_service.py:115-133`

`source_type='user_pdf'`, `source_ref=str(page_number)`, `title=NULL`.
Downstream citation render becomes `user_pdf/4` (per scout note). Plan §3.3
implies citations should be human-friendly.

`UserPdfIndex.filename` is captured at upload time — wire it through:

```sql
SELECT
    c.id AS chunk_id,
    c.pdf_index_id AS document_id,
    'user_pdf' AS source_type,
    CAST(c.page_number AS TEXT) AS source_ref,
    i.filename AS title,        -- JOIN user_pdf_index i ON i.id = c.pdf_index_id
    ...
FROM user_pdf_chunks c
JOIN user_pdf_index i ON i.id = c.pdf_index_id
WHERE c.pdf_index_id = :pdf_index_id
```

Citation reads `report.pdf/4` instead of `user_pdf/4`.

### 7. `page_count=None` allowed by schema but always set — `pdf_upload.py:88`

`PdfUploadResponse.page_count: Optional[int]` is permissive, but ingest always
sets `len(pages) >= 1` (else `PdfParseError`). Either tighten the schema to
`int` or document the None case. Tiny nit.

### 8. Cleanup job mid-upload race — `cleanup_user_pdfs.py:36-43`

03:00 cron + user uploading at 03:00:00 with a row that expired 1 second ago
→ user's ingest may attach to a row that gets deleted by the next statement.
Cascade also wipes their just-inserted chunks.

Plan accepts this risk. Realistically:
- expired rows are >30d old, the user just uploaded → `existing` path is rare
- the new insert uses default `expires_at = NOW() + 30d`, so it survives

The real edge is `_find_existing_index` returns a row that gets deleted
between SELECT and the response. Output is a stale id in `PdfUploadResponse`
that 500s on first message use.

**Fix (nice-to-have):** in `_find_existing_index`, filter
`WHERE expires_at > now()`. Same one-liner, cheap.

### 9. `pages` parameter type-hint loss — `user_pdf_service.py:121`

```python
async def _embed_and_persist_pages(self, pdf_index_id: int, pages: list) -> int:
```

`pages: list` should be `list[PageText]`. Cosmetic.

### 10. `superuser` fixture user_id collision in test #5 — `test_user_pdf_service.py:123-136`

Verifies isolation but assumes the fixtures give distinct ids; usually fine.
Stronger assertion: check `r1.pdf_index.id != r2.pdf_index.id AND r1.user_id !=
r2.user_id`. Already there. Good.

### 11. Backfill script — uncommitted on missing files — `scripts/backfill_pdf_hashes.py:51-58`

When `os.path.exists(pdf_path)` is false, we `continue` without setting
`file_hash`. Next run re-processes the same rows. Idempotent but wasteful for
large bases with many missing files. Consider tagging with sentinel
`'missing'` or a `pdf_missing_at` column — not blocking.

### 12. `PdfReader` resource scope — `pdf_parser_service.py:46`

`PdfReader(io.BytesIO(pdf_bytes))` — pypdf doesn't expose `.close()` and
relies on GC. Modern pypdf handles this, but for very large PDFs the BytesIO
copy doubles memory (25MB upload → 50MB peak). Streaming from `UploadFile`
direct to a temp file path + `PdfReader(path)` halves peak. **Defer** — fine
at current scale.

---

## Low Priority

### 13. `os.path.exists` instead of `pathlib` — `user_pdf_service.py:83`

Mixed `os.path` + `Path` across the module. Cosmetic.

### 14. Plan §"Temp files under per-user dir with 0700 permissions" not implemented

Upload router doesn't write to disk — bytes are in-memory. The plan's
"sandbox + 0700" mention is aspirational; cleanup job's `_sweep_temp_uploads`
walks `media/chat_uploads/` but nobody writes there. Either:
- Document that streaming-to-disk was dropped (KISS — fine for <25MB), OR
- Implement it. Current state: dead code in cleanup_user_pdfs.py.

### 15. Magic-bytes regex is exact-prefix — `pdf_upload.py:34, 47`

`b"%PDF-"` rejects PDFs that start with a BOM or whitespace (rare in the wild
but RFC-permitted). pypdf will still parse them. Probably fine — strict is
safer. Not a fix; just an observation.

### 16. Test `db_session` ordering — `test_pdf_match_service.py:9-17`

`async def _make_report(db, ...)` without `@pytest.mark.asyncio` decorator on
the helper is fine (helpers don't need it), but `test_sha256_hex_*` are sync
and the first two tests don't use the db fixture. Inconsistent style. Cosmetic.

---

## Edge Cases Flagged (Scout)

| # | Edge case | Status |
|---|-----------|--------|
| 1 | Pre-read size DoS | High — fix #1 |
| 2 | Per-user isolation | OK — find_match filters user_id; retrieval scoped by pdf_context_id; PATCH validates ownership; UNIQUE(user_id, pdf_hash) per-user |
| 3 | Concurrent same-hash upload race | High — fix #3 |
| 4 | pypdf swallow vs propagate | OK — broad `except` in `extract_pages:59-61` only swallows per-page failures, returns empty for that page; module-level open raises `PdfParseError` cleanly |
| 5 | Stale file_hash on disk | Medium — #4 |
| 6 | Split inverted vs plan | High — #2 |
| 7 | Opaque citation source | Medium — #6 |
| 8 | Cleanup-job race window | Medium — #8 |
| 9 | TTL not slid on re-upload | High — #5 |
| 10 | LOC budget | All under: match 36/100, parser 85/120, service 153/180, router 138/150, cleanup 61/80 ✓ |
| 11 | Test gaps | Hallucination test deferred (plan accepts); recommend cheap integration test below |

### Integration test gap (recommend cheap addition)

Current router tests stub `UserPdfService.ingest` — they prove HTTP wiring but
don't catch retrieval-merge regressions. **Add one end-to-end test:**

```python
async def test_e2e_pdf_upload_then_message_uses_pdf_context(
    client, auth_headers, db_session, patch_embeddings, patch_llm
):
    # upload (with patched embed/LLM but real ingest)
    # send message
    # assert assistant message citations include source_type="user_pdf"
```

Catches: retrieval not receiving `pdf_context_id`, SQL typo in
`_search_hybrid`, score-sort regression. ~30 LOC, no real Gemini key.

---

## Positive Observations

- Per-user isolation is **belt-and-suspenders** (user_id in match query, user_id
  in PdfIndex insert, ownership check in PATCH, scoped by pdf_index_id in
  retrieval).
- Idempotency on re-upload is correct (apart from race in #3 and TTL #5).
- `clean_text` is small, tested, and right-sized — hyphen repair before
  whitespace collapse is the correct order.
- `_FakeEmbeddings` in unit tests is the right shape — deterministic, no
  network, dimensional match enforced.
- HNSW index params (`m=16, ef_construction=64`) match phase 01 — consistent.
- Migration is clean and reversible. FK `pdf_context_id` SET NULL on user_pdf_index
  deletion matches the cleanup-job semantics.
- Python-side `_default_expires_at` + PG `server_default` dual approach is
  exactly the right call for sqlite-portable ORM tests.
- KB-only fast path (`pdf_context_id is None`) preserves Phase 02 behavior
  with zero overhead.

---

## Recommended Actions

**Must-fix (block merge):**
None.

**Should-fix (before next phase):**
1. Atomic insert race (#3) — try/except IntegrityError + re-query
2. Pre-read streaming size check (#1) + bump nginx cap to 26M
3. TTL slide on re-upload (#5)
4. Decide & document KB/PDF split direction (#2)
5. Pass filename as title in PDF citation rows (#6)

**Nice-to-have (sometime):**
- File-on-disk hash re-verification (#4)
- `expires_at > now()` filter in `_find_existing_index` (#8)
- E2E integration test for PDF → message flow
- Decide on streaming-to-disk story (#14) — either implement or remove dead
  cleanup code

---

## Metrics

- LOC budget: All under (61–153 vs 80–180 budget) ✓
- Type coverage: minor (`pages: list` → `list[PageText]`) #9
- Linting: no issues observed in reviewed files
- Tests: 81/81 chat (P3 adds 27 new); coverage of retrieval merge thin

---

## Open Questions

1. **Plan §27 says "2 KB + 3 PDF" — was the implementation's `pdf_k = (top_k+1)//2`
   intentional inversion, or a typo? Free tier top_k=3 produces 2 PDF + 1 KB.**

2. **What's the policy when matched_report.pdf_path is missing AND we already
   matched? Currently silently falls back to uploaded bytes — should we log a
   data-integrity warning so ops sees orphaned UserReport rows?**

3. **Is the `media/chat_uploads/` temp-file sweep dead code (no writer
   exists) — or planned for a future deferred-parse path?**

4. **Should re-uploading slide TTL (#5)? Brainstorm says "30d TTL auto-clears"
   without specifying refresh semantics.**

5. **Manual hallucination test (plan todo line 207) — when is the gate for
   running it? Before P4 UI or before any prod deploy?**
