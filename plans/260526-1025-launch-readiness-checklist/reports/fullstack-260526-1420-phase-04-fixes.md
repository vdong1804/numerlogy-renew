# Phase 04 Critical + High Fixes Report

## Fix Summary

**C1 — http_http_status typo** (`orders.py:145`)
- `http_http_status.HTTP_400_BAD_REQUEST` → `http_status.HTTP_400_BAD_REQUEST`
- Was NameError → 500; now returns correct 400.

**H1 — ILIKE wildcard injection** (`orders.py:53-56`, `csv_export_service.py:63-66`)
- New helper `app/utils/query.py::escape_like(s)`: escapes `\`, `%`, `_` before wrapping in `%…%`.
- Both `_build_search_stmt` and `_build_query` now call `.ilike(f"%{escape_like(...)}%", escape="\\")`.
- Added `max_length=200` on `email`/`ref_code` Query params in both `list_orders` and `export_orders`.

**H2 — CSV formula injection** (`csv_export_service.py`)
- Added `_safe_csv_cell(val)`: prefixes `'` if value starts with `=+−@\t\r`.
- Applied to all 9 cells in `writerow`.

**H3 — DatePicker Bangkok vs UTC** (`order-search-form.tsx`)
- Added `toIsoWithBangkokTz(dateStr, endOfDay)` helper.
- `date_from` → `YYYY-MM-DDT00:00:00+07:00`, `date_to` → `YYYY-MM-DDT23:59:59+07:00`.
- `toDateInputValue()` strips ISO back to `YYYY-MM-DD` for display.
- Backend comment added in `export_orders` params documenting contract.

**H4 — CSV 10k headroom** (`csv_export_service.py:23`)
- Added inline comment: "INTENTIONAL: bounded 10k… For >10k, refactor to streaming row-by-row."

**H5 — exportOrdersCsv JSON error UX** (`admin-dashboard-api.ts:122-127`)
- On `!res.ok`: parse JSON → extract `detail` field → `throw new Error(detail)`.
- UI's existing `setError((err as Error).message)` in `handleExportCsv` now shows readable message.

**Bonus — refunded_at in Order model** (`app/db/models/order.py`)
- Added `refunded_at: Mapped[Optional[datetime]]` column (confirmed by migration 0008).
- Removed `getattr(order, "refunded_at", None)` fallback in csv_export_service; uses `order.refunded_at` directly.

## Verify Results

- Backend import: `OK`
- Tests: `17 failed, 173 passed` — matches pre-existing baseline, no regressions.
- Frontend build: clean (sitemap generation complete).

## Blockers

None.

## Unresolved Qs

- Order model `admin_notes` column (also added by migration 0008) not yet mapped in model — not needed by any current query but worth syncing for completeness (deferred, YAGNI).
