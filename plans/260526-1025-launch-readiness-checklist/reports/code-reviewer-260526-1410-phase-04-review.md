# Code Review — Phase 04 (Admin Search/Export + Image + Runbooks)

Date: 2026-05-26 | Reviewer: code-reviewer

## Overall Score: 7.5/10

Solid implementation. Auth, param binding, BOM, runbooks correct. ONE compile-breaking typo + a handful of input-validation gaps to address before go-live.

---

## Critical Issues (1)

1. **`orders.py:145` — `http_http_status` typo → NameError at runtime.**
   When CSV export exceeds 10k rows, the `except ValueError` branch crashes with `NameError: name 'http_http_status' is not defined`, hiding the real 400 message and returning 500. Likely from an accidental sed/rename pass. Fix: `http_status.HTTP_400_BAD_REQUEST`.

## High Issues (5)

1. **SQL LIKE wildcard injection** — `orders.py:54,56` & `csv_export_service.py:64,66`. User-supplied `email`/`ref_code` go straight into `ilike(f"%{x}%")` without escaping `%` or `_`. Params themselves are bound (no SQLi), but an attacker can submit `%` to scan the whole table cheaply (perf DoS, info-leak vector). Mitigate: `value.replace("\\","\\\\").replace("%","\\%").replace("_","\\_")` + `escape="\\"` arg on `.ilike()`. Also enforce `max_length` via `Query(..., max_length=128)`.

2. **CSV injection (Excel formula)** — `csv_export_service.py:121`. `product_names`, `ref_code`, `user_email` written raw; if any starts with `=`/`+`/`-`/`@`/`\t`/`\r`, Excel evaluates it as a formula on open. Prefix risky cells with `'` or wrap in `="..."`. Real risk because `snapshot_name` originates from product input/admin-editable text.

3. **DatePicker timezone mismatch** — `order-search-form.tsx:81-95` sends bare `YYYY-MM-DD`. FastAPI parses as naive datetime at 00:00 UTC; user in Bangkok (UTC+7) picking "26/05" misses 7h of local orders at start and includes 7h of next-day at the end. Either: backend converts naive → +07:00 before compare, OR frontend emits ISO with `+07:00`. Document expected behavior.

4. **CSV export auth via fetch is fine, but no Content-Length / streaming** — `csv_export_service.py:97` calls `.all()` materializing 10k rows in memory plus serialized buffer. ~10k rows × ~200B ≈ 2MB — acceptable, but flag if limit raised. Consider true streaming (`yield writer rows`) for headroom.

5. **`exportOrdersCsv` swallows JSON error body** — `admin-dashboard-api.ts:124`. Backend returns `{"detail": "Export would return …"}` JSON; `res.text()` returns the full JSON blob which surfaces as `{"detail":"…"}` in UI. Parse JSON first when `Content-Type: application/json`.

## Medium (6)

- `orders.py` LOC 249 (over 200-line guideline) — split helpers + export into separate module.
- `csv_export_service.py:119` `getattr(order, "refunded_at", None)` — `Order` model already has the column post-Phase-02; replace with direct attribute access (the getattr fallback hides typos).
- `index.tsx:71-73` `useEffect` depends on `filters` (object identity) — every `handlePageChange` causes refetch which is correct, but `EMPTY_FILTERS` object literal at module scope is fine; double-check no extra re-renders via React DevTools.
- `Banner.tsx:227` zodiac still raw `<img>` — `image-audit.md` documents the defer; acceptable, but mark `loading="lazy"` to avoid blocking.
- `go-live-runbook.md` Step 16: env var checklist is good but missing `TURNSTILE_SECRET_KEY`, `JWT_*`, `DATABASE_URL`.
- `post-launch-monitoring.md` lacks RTO/RPO targets and on-call rotation schedule.

## Low (4)

- `OrderSearchForm` Enter on date picker doesn't trigger search (`handleKeyDown` only on text inputs) — minor UX.
- `csv_export_service.py` `_build_query` duplicates filter logic with router `_build_search_stmt` — extract once (DRY).
- `image-audit.md` lists `adalash_thanh2.png` as possibly unused; verify before next deploy to shrink bundle.
- Status badge in `index.tsx` colors only `paid` distinctly — `refunded`/`failed` should use destructive variant.

## Strengths

- Token correctly via `Authorization: Bearer` header (not URL).
- All admin endpoints gated by `get_current_superuser`.
- UTF-8 BOM for Excel VN — correct, well-commented.
- Param binding via SQLAlchemy: SQL injection blocked at driver level.
- 10k row limit + structured logging on export.
- `next/image` migration sound for LCP candidates; `priority` set; image-audit doc thorough.
- Runbooks bilingual, actionable, include rollback + comms plan.

## Top 3 Actions

1. **Fix `http_http_status` typo** (`orders.py:145`) — blocker, one-line fix.
2. **Escape `%`/`_` in ILIKE filters + add `max_length` Query constraint** — prevents perf-DoS and unbounded scans.
3. **Sanitize CSV cells against Excel formula injection** — prefix `=+-@\t\r` with `'`.

## Unresolved Questions

- Should `refunded_at` be added to `Order` model directly or kept in `meta` JSON? `getattr` fallback suggests inconsistency.
- DatePicker timezone contract: backend-side TZ shift or frontend ISO with offset? Pick one and document.
- Is there a frontend test for `exportOrdersCsv` Blob download? Browser CORS for `Content-Disposition` only works if backend sets `Access-Control-Expose-Headers` — verify.
- `EXPORT_ROW_LIMIT=10_000` — confirm with product whether monthly exports may exceed; if yes plan async/queued export.
