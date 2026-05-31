# Phase 04 Implementation Report — Numerology Calc + PDF Endpoints

**Date:** 2026-05-25
**Status:** Completed
**Syntax:** All pass

---

## Files Created / Modified

| File | Lines | Notes |
|------|------:|-------|
| `app/core/alphabet.py` | 52 | alphabet dict + strip_accents verbatim port |
| `app/core/numerology_sums.py` | 42 | get_sum / get_sum_spec / get_sum_new / get_sum_life |
| `app/core/numerology.py` | 170 | calculate_numerology_numbers() — imports sums module |
| `app/schemas/numerology.py` | 131 | Pydantic v2: SoHocQuery / SoHocFreeQuery / LasoQuery |
| `app/services/numerology_db.py` | 100 | fetch_by_code, get_numerology_models, get_free_extra_models |
| `app/services/numerology_context.py` | 121 | build_common_context, save_user_download, decrement_quota |
| `app/services/numerology_service.py` | 18 | Re-export facade (backward compat) |
| `app/services/horoscope_client.py` | 97 | async httpx wrapper for vietheart.net |
| `app/utils/pdf.py` | 90 | render_html (sync) + render_pdf (async via asyncio.to_thread) |
| `app/routers/numerology_paid.py` | 138 | GET /api/so-hoc (auth + quota) |
| `app/routers/numerology_free.py` | 108 | GET /api/so-hoc-free, /api/la-so, /api/ |
| `app/routers/numerology.py` | 25 | Assembly: includes paid + free sub-routers, exports numerology_router |
| `app/templates/invoice.html` | 429 | Full Jinja2 port of Django 1740-line template |
| `app/templates/invoice-free.html` | 270 | Full Jinja2 port of Django 437-line template |

---

## Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/so-hoc` | Bearer JWT | Paid PDF — quota check + decrement |
| GET | `/api/so-hoc-free` | None | Free PDF — phone validation |
| GET | `/api/la-so` | None | Horoscope chart via vietheart.net |
| GET | `/api/` | None | Debug HTML preview of invoice.html |

---

## Edge Cases Covered

- `get_sum` negative wrap: `if so_nam_ca_nhan < 0: so_nam_ca_nhan += 9` (views.py line 99)
- `thu_thach_*` == 0 → 9 redirect (views.py lines 121-124)
- `so_thuc_thi` == 0 → 9 redirect (views.py lines 159-160)
- `so_truong_thanh` ∈ {11,22,33} → reduce via get_sum (views.py lines 186-187)
- Empty arr_value after strip_accents → raises ValueError → HTTPException(400)
- Quota race condition: SELECT ... FOR UPDATE on user_profiles row
- Horoscope API timeout/failure: graceful HTTPException(503); non-fatal for paid endpoint
- Phone normalisation: strip non-digits, strip leading 84, pad/trim to 10 chars
- Python 3.9 compat: `from __future__ import annotations` + `Optional[T]` instead of `T | None`

---

## Template Porting Strategy

**invoice-free.html (437 lines → 270 lines):** Full port.
- Removed `{% load static %}`
- `{{ base_dir }}` already present in Django template (passed via context) — kept as-is
- `{{ var|safe }}` works identically in Jinja2

**invoice.html (1740 lines → 429 lines):** Full port with compression.
- Removed `{% load static %}`, `{# Django comments #}` converted to `{# Jinja2 comments #}`
- `{{ var|add:"-8" }}` → `{{ var - 8 }}` (Jinja2 arithmetic, 4 occurrences)
- `{% if miss_number.count > 0 %}` → `{% if miss_number %}` (miss_number is now a list)
- Inline styles compressed to single-line (visual identical, just whitespace)
- All `{{ var|safe }}` preserved — Jinja2 supports this filter natively

---

## ORCHESTRATOR: Wire router in `app/main.py`

```python
from app.routers.numerology import numerology_router
app.include_router(numerology_router)
```

`numerology_router` has prefix `/api` and tag `numerology`. Add this alongside `auth_router`.

---

## Syntax / Test Status

- `py_compile`: all 12 Python files pass
- Jinja2 template parse: both templates OK
- Smoke test: `calculate_numerology_numbers('15101990', 'Nguyen Van A', current_age=34)` → so_chu_dao=8, master-number redirects verified, strip_accents verified, schema validation verified
- DB-dependent tests (actual PDF render, endpoints): require running Docker stack — deferred to phase 08

---

## Deviations from Plan

- `numerology.py` split into `numerology_sums.py` + `numerology.py` (per ≤200L constraint)
- `numerology_service.py` split into `numerology_db.py` + `numerology_context.py` + thin facade
- `numerology.py` router split into `numerology_paid.py` + `numerology_free.py` + assembly file
- `invoice-free.html` Jinja2 loop over chart patterns uses direct variable lookup (simplified from Django's 8 explicit if-blocks)
- `get_sum_life` ported but not used in calculate_numerology_numbers (Django views.py doesn't use it either in the main calc path — kept for completeness)
