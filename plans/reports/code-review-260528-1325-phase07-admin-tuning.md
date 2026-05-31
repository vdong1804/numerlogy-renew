# Code Review — Phase 07 Admin Tuning (Chatbot RAG)

**Date:** 2026-05-28
**Scope:** new + modified files only (backend + frontend)
**Score:** **7.8 / 10**

---

## Summary

Solid, well-organised phase. Migration, ORM, service, router, schemas all line up. Auth-guard pattern (parent `admin_router` injects `Depends(get_current_superuser)`) is verified — there is no auth hole on any new route. Service files are tight, audit-log is real, and analytics is pure ORM (no SQL-injection surface). Tests are meaningful.

Findings: 0 critical, 4 high, 6 medium, several low/nits. Primary risks are around the upload size buffer (in-memory), prompt-history audit semantics (snapshot ordering), and a couple of correctness/cache nits.

---

## Critical — 0

None.

---

## High — 4

### H1. Upload buffer is fully in-memory (DoS exposure)
**File:** `app/routers/admin/chatbot.py:65-74`, `app/services/chat/admin_kb_service.py`
**Issue:** `_read_upload()` accumulates up to 100 MB into a `bytearray`, then passes `bytes(buf)` (doubling memory at the conversion). Under concurrent admin uploads — or a compromised admin token — N×200 MB is plausible. PDF parsing on top of that creates further allocations (pypdf builds page text in memory).
**Impact:** Single Gunicorn worker OOM-kills with 2-3 simultaneous max-size uploads.
**Recommended fix (any one):**
- Stream to a `tempfile.SpooledTemporaryFile(max_size=10 * 1024 * 1024)` and pass a file-like object down (pypdf + python-docx both accept it).
- Drop limit to 25 MB (numerology docs are small in practice) and add a per-admin upload rate-limit.
- Run uploads through a `Semaphore(2)` at the router level so concurrency is bounded.

### H2. `get_db` auto-commits on success → mutating GETs persist
**File:** `app/deps.py:20-28`, all admin chatbot read endpoints
**Issue:** `get_db` does `await session.commit()` at the end of the request even for pure GETs. The new GET endpoints (`/prompt`, `/conversations`, `/analytics/overview`) are read-only at the ORM layer, so this is harmless today. BUT: `_serialize_doc` is called from `list_kb_documents` and reads `doc.doc_metadata or {}` — if the relationship were ever lazily expanded by Pydantic, an implicit refresh inside an open transaction could surface. This is a latent project-level concern that this phase doesn't introduce — flag it as a follow-up.
**Action:** No change needed in this phase. Track for a future "tighten get_db" task: prefer a `begin()` block scoped to writes only.

### H3. Audit snapshot writes the *previous* row but only after mutation in some paths
**File:** `app/services/chat/prompt_settings_service.py:100-149`
**Issue:** In `update()`, the history row is added BEFORE the in-place mutation (good). But:
1. The initial-insert branch (lines 109-124) writes a history row with `version=1` *equal to* the new value — that's a "creation event" entry, fine, but the test (`test_update_creates_row_and_history`) asserts `hist[0].value == "first version"`. Consider clarifying intent: is history a "values prior to change" log or a "change events" log? Current impl mixes both (init = current value snapshot; update = prior-value snapshot; delete = prior-value snapshot). That makes "rollback to history entry N" ambiguous.
2. `existing.updated_by` is read for the audit row's `changed_by` — but `changed_by` should arguably be the user who triggered the change, not the prior author. The current value (prior `updated_by`) is misleading on the timeline.
**Recommended fix:** Make `changed_by` = the current `updated_by` parameter (i.e. who changed it) and add a `previous_updated_by` column if attribution of the prior author is needed. At minimum, doc the convention in the model docstring.

### H4. `_serialize_doc` reads `doc.created_at`/`updated_at` before refresh in `upload_kb_document`
**File:** `app/routers/admin/chatbot.py:96-130`
**Issue:** On Postgres `server_default=NOW()` populates the timestamps but ORM-loaded value only appears after a `refresh()`. The router does refresh (`await db.refresh(doc)` at line 121) — good. But the comment on line 119 says "SQLite skips RETURNING, leaving created_at / updated_at unloaded otherwise." That's true; the call is necessary. Just confirm `TimestampMixin` includes both columns with `server_default` set (it does, in `app/db/models/mixins.py` — not re-read here but expected per other models). **No fix; verify in QA the refresh isn't redundant on PG.**

---

## Medium — 6

### M1. `_extract_txt` masks UTF-8 errors silently with latin-1 fallback
**File:** `app/services/chat/admin_kb_service.py:165-172`
**Issue:** Falling back to latin-1 (which never raises) means malformed UTF-8 is silently decoded to mojibake. The chunker will happily embed garbage and the chatbot will retrieve garbage.
**Recommended fix:** After UTF-8 fail, raise `ExtractedEmpty("file is not valid UTF-8 — re-export from your editor")` rather than guessing. Or log a warning when the latin-1 path activates.

### M2. File extension trusted; no magic-byte sniff
**File:** `app/services/chat/admin_kb_service.py:102-128`
**Issue:** A `.pdf` upload whose body is a TXT file would hit `_extract_pdf` and fail with `PdfParseError → ExtractedEmpty` — that's fine (graceful 422). A `.docx` upload whose body is a renamed binary will fail similarly. Risk is low (admin-only endpoint) but `python-magic`/`filetype` lib would let the service return a clearer error and prevent confused-deputy file kind reporting in metadata.
**Recommended fix:** Optional. Add magic-byte check only if mistaken uploads become a UX issue. Acceptable as-is given admin-only access.

### M3. `messages_by_day` SQL: `func.date(created_at)` is timezone-naive
**File:** `app/services/chat/chat_analytics_service.py:160-175`
**Issue:** `func.date(ChatMessage.created_at)` on PG calls `DATE(timestamptz)` which casts using the session TimeZone setting. If the PG session TZ is not UTC, daily buckets are wrong. Same concern in `top_questions` (no date involved there — OK).
**Recommended fix:** Use `func.date(func.timezone("UTC", ChatMessage.created_at))` or `func.to_char(..., "YYYY-MM-DD")` with explicit AT TIME ZONE. Low impact today but causes nasty Monday-morning surprises when ops change session TZ.

### M4. `semantic_cache_hit_rate` formula is odd
**File:** `app/services/chat/chat_analytics_service.py:119-123`
**Code:** `hit_rate = hits / (hits + total_messages)`
**Issue:** That's not a hit rate. A "hit rate" is `hits / (hits + misses)` where misses ≈ assistant messages that *didn't* hit cache. Using `total_messages` (which includes user rows + non-cacheable rows) skews the denominator down → rate looks artificially high *and* low simultaneously depending on free/paid mix.
**Recommended fix:** `hit_rate = hits / max(hits + assistant_messages_count, 1)`; or just expose raw `hits` and `entries` and let the UI compute its own ratio.

### M5. `top_questions` groups by exact-match `content` — Vietnamese variants miss
**File:** `app/services/chat/chat_analytics_service.py:177-192`
**Issue:** "Số mệnh 8" vs "số mệnh 8" vs "Số mệnh 8?" are 3 rows. The dashboard will show noisy near-duplicates. Acceptable for v1 but worth tracking. Also: no length cap — a 10 KB pasted question becomes a giant table row in the JSON response.
**Recommended fix:** `func.left(content, 200)` in the SELECT, plus optional `lower(content)` for grouping. Keep raw content for citation if needed.

### M6. `KbDocumentOut.metadata` is a Pydantic v2 reserved-style name
**File:** `app/schemas/chat/admin.py:22`
**Issue:** Pydantic v2 reserves the `model_` namespace and emits a `UserWarning` when a field shadows `BaseModel.metadata` (which it doesn't, but `model_metadata` would). The current name `metadata` is fine. **Non-issue confirmed.**

---

## Low / Nits

- **L1.** `prompt_settings_service._cache` is a module-level dict — works per-process. With multiple Gunicorn workers, an admin update on worker A leaves worker B serving stale up to 60s. Acknowledged in code comments — fine. Long-term: move to Redis or fire an internal pub/sub.
- **L2.** `prompt_settings_service.get_override` re-reads cache inside the lock without TTL check on the first peek (line 78). Fine — the inner re-check (line 85) handles it. Slightly confusing to read; consider a docstring note.
- **L3.** `admin_kb_service._extract_docx`: catches `Exception` (`# noqa: BLE001`) — would be cleaner to catch `docx.opc.exceptions.PackageNotFoundError` and let other errors bubble. Minor.
- **L4.** `chatbot.py:96` `response_model=dict` everywhere — the typed Pydantic models exist but are dumped to dict at the end. This loses OpenAPI fidelity; clients only see "additionalProperties". Consider `response_model=KbUploadResponse` etc. (matches "flat JSON" choice — `response_model_exclude_unset` if needed).
- **L5.** `grant_addon` (chatbot.py:338-387): no idempotency token. Double-click on admin UI = 2 grants. Risk is real but limited (admin grants are deliberate and low-frequency). Add a server-side lock per `(user_id, package_id)` for 5s, or surface a confirmation dialog in UI (the UI page is deferred so not blocking).
- **L6.** `chatbot.py:108` swallows `RuntimeError` from `admin_kb_service.ingest_upload` only via `UnsupportedFileType` / `ExtractedEmpty`. If python-docx isn't installed at runtime, `RuntimeError("python-docx not installed...")` returns a generic 500. Add a `RuntimeError → 500 with detail` branch or precondition-check at module import.
- **L7.** `chatbot.py:155` N+1 batched correctly with `IN` clause. Good.
- **L8.** Frontend `kb-upload-form.tsx` reads `localStorage.getItem('admin_access_token')` directly; the project has `admin-api` helpers (`getJson`, `del`) — use a `postFormData` helper so the auth header logic is centralised. Currently a divergence with the rest of admin code.
- **L9.** Frontend `kb-upload-form.tsx:54` builds query string with raw `encodeURIComponent(title)` then concatenates — fine, but `URLSearchParams` would match `kb.tsx` style.
- **L10.** Frontend `index.tsx:90` divides by zero if `data` exists but rate is `NaN`. Backend already clamps to `0.0` so safe; cosmetic.
- **L11.** `chat_analytics_service.py:159` `_daily_breakdown` builds a label `day` that becomes `str(d)` in the dataclass — on PG `func.date(...)` returns `date` whose `str()` is `YYYY-MM-DD`, on SQLite it's a string already. Cross-DB safe but inconsistent typing under the hood.

---

## Specifically Asked

| Question | Finding |
|---|---|
| Authorization holes? | None. `admin_router` enforces `Depends(get_current_superuser)` at the parent level (`app/routers/admin/__init__.py:21`). Per-route `Depends(get_current_superuser)` on writes is redundant but harmless. |
| SQL injection in analytics? | None. All queries use `select()` + ORM-typed columns + parametrised `func.coalesce()`. The `tier` query param flows through `where(ChatMessage.tier == tier)` (parameterised). |
| Resource leaks (upload, sessions)? | `_read_upload` does not close `UploadFile.file` explicitly. FastAPI closes it on request end via Starlette's `BackgroundTasks`, but in pathological cases (exception before read completes) a temp file may linger. Low risk. Sessions are scoped via `get_db` async context — clean. |
| Cache staleness in prompt_settings? | Single-process: tight. Cross-process: documented 60s window. **Suggest:** add `prompt_settings_service.invalidate_cache()` call in `delete()` for the `key=None` path too (currently only invalidates the specific key — fine, but document). |
| Race on addon grant? | Yes — L5 above. Click-debounce in UI + server-side dedupe window recommended. |
| 100 MB DoS? | **High concern — see H1.** Reduce ceiling or stream to disk. |
| Frontend XSS? | Conversation viewer is deferred. `kb-document-list.tsx` renders `row.original.title` as React text node (auto-escaped by React) — safe. Top questions list (`index.tsx:164`) renders `q.question` as text — safe. **No HTML injection paths.** |
| File extension trust? | See M2. Acceptable for admin-only. |
| Unawaited coroutines? | None found. `tester` already ran — backed up by passing suite. |
| Pydantic `from_attributes` for ORM outputs? | `KbDocumentOut`, `PromptHistoryEntry`, `ConversationListItem`, `ConversationMessage` all set `model_config = ConfigDict(from_attributes=True)`. `ConversationDetailOut` and `KbUploadResponse` don't — they're composed structures built explicitly, not from ORM. **Fine.** |
| GEMINI_API_KEY unset? | `EmbeddingService.client` raises `EmbeddingError("GEMINI_API_KEY is not configured")` on first use. Admin KB upload would surface as 500. **Suggest:** catch `EmbeddingError` in `upload_kb_document` and return `503 detail="embedding service unavailable"` for a clearer admin UX. |

---

## Positive Observations

- Migration is symmetric; down-paths drop indexes before tables. Clean.
- Service files all ≤200 LOC, single-responsibility, well-documented top-line docstrings.
- Audit log is real (history rows on insert/update/delete), not "TODO".
- Idempotent KB upload via `source_ref = f"{admin_id}-{filename}"` + `KbIngestionService._replace_chunks` content-hash short-circuit (line 137) — avoids spurious prompt-cache invalidation. Strong design.
- `_read_upload` uses streaming read with chunked size-check — correct early-413 (good, just bound the buffer differently per H1).
- Tests cover happy path + auth guard + 415/422/404 + idempotency + version bump + cache TTL + delete-resets-default. 36 tests is reasonable; integration + service-unit split is healthy.
- Prompt builder's `resolve_system_prompt(None)` fallback is centralised — both `build_prompt` and any future prompt-cache key code use the same rule. Good.
- Frontend uses `ContentTable`, `AdminLayout`, `DashboardStatCard` — matches house style.
- `get_current_superuser` parent dependency confirmed: admin chatbot routes correctly inherit the guard. No 403/401 holes.

---

## Recommended Actions (Prioritised)

1. **H1** — Reduce upload limit OR stream to spooled temp file. Add `Semaphore(2)` if keeping 100 MB. (1-2 h)
2. **H3** — Document audit-log semantics; consider adding `previous_updated_by` column or rename `changed_by` semantics. (30 min + migration if column added)
3. **M3** — Wrap `func.date()` with explicit UTC TZ. (10 min, 1 LOC change × 2 sites)
4. **M4** — Replace hit-rate formula with `hits / (hits + assistant_count)` or expose raw counts. (15 min + test update)
5. **L4** — Switch `response_model=dict` to typed Pydantic responses for OpenAPI schema fidelity. (30 min)
6. **L5** — Server-side 5-second dedupe window on `grant_addon`. (20 min)
7. **L8** — Centralise admin auth header in a `postFormData` helper. (15 min)

Total fix budget for High items: ~2 hours.

---

## Metrics

- Type coverage: ~95% (all new Python uses `Mapped[]` and Pydantic typing; one `response_model=dict` regression noted)
- Test coverage: backend 36 new tests, full chat+admin suite 215 passed / 4 skipped (reported)
- Linting issues: presumed clean (compile clean reported); not re-run by this review
- LOC budget: all new files ≤200 LOC; `chatbot.py` exactly 200 (acceptable)

---

## Unresolved Questions

1. Is the 100 MB ceiling a product requirement, or inherited from a generic "be generous" assumption? If admin docs are typically <10 MB, dropping to 25 MB removes H1 cleanly.
2. Should `grant_addon` re-use the existing payment-processing path (UserPayment row + ChatAddonPurchase) for accounting consistency, or stay as a comp-grant with `payment_id=NULL`? Current code does the latter — confirm with finance/billing.
3. `PromptCacheService.invalidate_for_chunks` is referenced in the docstring of `prompt_settings_service.py:21` but not called from `update()` / `delete()`. Is admin expected to manually invalidate after prompt edits, or should `update()` fire-and-forget invalidate the cache too? Right now Gemini cache stays stale until natural TTL.
4. Conversation viewer page deferred — confirm there is no admin route emitting raw `content` as HTML anywhere else (a quick grep of existing admin pages was not part of this scoped review).
