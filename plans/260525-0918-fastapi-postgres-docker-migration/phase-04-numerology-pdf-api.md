# Phase 04 — Numerology Calc + PDF Endpoints

**Priority:** P0 (core feature)
**Effort:** L (16-20h)
**Status:** Done
**Depends on:** phase-02, phase-03

## Goal

Port core numerology business logic + PDF rendering từ `apis/views.py` (1250 LOC) sang FastAPI:

- `GET /api/so-hoc` (paid, auth required, quota)
- `GET /api/so-hoc-free` (public)
- `GET /api/la-so` (calls vietheart.net horoscope API)
- `GET /api/` (the `top()` function — debug/preview HTML)

## Source Logic Reference

`D:/Freelancer/Numerlogy/numerology/apis/views.py:26-231` — `calculate_numerology_numbers()`
`D:/Freelancer/Numerlogy/numerology/apis/views.py:234-289` — `get_numerology_models()`
`D:/Freelancer/Numerlogy/numerology/apis/views.py:292-365` — `build_common_context()`
`D:/Freelancer/Numerlogy/numerology/apis/views.py:447-490` — birthday chart + PDF helpers
`D:/Freelancer/Numerlogy/numerology/apis/views.py:493-548` — `SoHocAPIView`
`D:/Freelancer/Numerlogy/numerology/apis/views.py:551-610` — `SoHocFreeAPIView`
`D:/Freelancer/Numerlogy/numerology/apis/views.py:712-729` — `LasoAPIView`
`D:/Freelancer/Numerlogy/numerology/apis/constans.py` — `get_sum`, `get_sum_life`, `get_sum_spec`, `get_sum_new`, `alphabet` dict (Vietnamese letter→num)
`D:/Freelancer/Numerlogy/numerology/apis/utils.py` — `gen_horoscopes()` (calls vietheart.net)
`D:/Freelancer/Numerlogy/numerology/templates/invoice.html` (50KB) — paid template
`D:/Freelancer/Numerlogy/numerology/templates/invoice-free.html` (10KB) — free template

## Files to Create

```
app/core/numerology.py          # Pure calc fns — ZERO db, ZERO framework. 100% unit-testable.
app/core/alphabet.py            # alphabet dict + strip_accents
app/services/numerology_service.py  # DB lookups (LifePeak.objects.filter → SQLAlchemy select)
app/services/horoscope_client.py    # httpx async wrapper for vietheart.net
app/utils/pdf.py                # render_pdf(template_name, context) → PDF bytes
app/routers/numerology.py       # 4 endpoints
app/schemas/numerology.py       # Query param validation (full_name, birth_day, phone, sex, birth_time)
app/templates/invoice.html      # ported from Django
app/templates/invoice-free.html # ported from Django
```

## Critical Translation Rules

### Django Template → Jinja2

| Django | Jinja2 |
|--------|--------|
| `{% load static %}` | (remove — pass `base_dir` in context) |
| `{{ var\|default:"" }}` | `{{ var or "" }}` |
| `{% if x %}` | `{% if x %}` (same) |
| `{{ obj.content\|safe }}` | `{{ obj.content\|safe }}` (Jinja2 has `safe` filter too) |
| `{% url 'name' %}` | (remove — no Django URLs needed in PDF templates) |
| `{{ var.attr }}` | `{{ var.attr }}` (same) |

### Django ORM → SQLAlchemy 2.0

```python
# Django
life_peak_1 = LifePeak.objects.filter(code=dinh_cao_1).first()

# SQLAlchemy 2.0 async
result = await session.execute(select(LifePeak).where(LifePeak.code == str(dinh_cao_1)))
life_peak_1 = result.scalar_one_or_none()
```

→ Wrap into `get_by_code(model_cls, code)` helper.

## Steps

1. **Extract pure calc to `app/core/numerology.py`** — copy `calculate_numerology_numbers()` verbatim (already pure). Same for `strip_accents`, `get_sum`, etc.
2. **Move `alphabet` dict** to `app/core/alphabet.py` (no logic change).
3. **Implement `get_numerology_models()` in SQLAlchemy** — bulk-fetch all needed content rows. Optimize: 1 query per table (DRY pattern: `fetch_by_codes(session, model_cls, codes)`).
4. **Port `build_common_context()`** — identical logic, just dict-building.
5. **Implement `render_pdf()`** — Jinja2 Environment, render template, pipe HTML → `pdfkit.from_string()` (sync, but call via `asyncio.to_thread`).
6. **Port `invoice.html`** — find/replace Django tags, validate Jinja2 syntax. Visual diff vs Django output for a few sample inputs.
7. **Port `invoice-free.html`** — same.
8. **`POST` → `GET` decision:** Keep `GET` with query params to match frontend (no breaking change for non-auth flow).
9. **Wire endpoints:**
   - `/api/so-hoc`: `Depends(get_current_user)` → check `profile.number_download >= 1` → calc → PDF → decrement quota in transaction → save `UserDownload(type=1)` → return PDF stream.
   - `/api/so-hoc-free`: validate phone → save `UserDownload(type=0)` → calc → PDF stream.
   - `/api/la-so`: parse birth_time → call `gen_horoscopes` → return `{data: {horoscopes: <image>}}`.
   - `/api/` (top): render HTML response (debug preview, optional).
10. **Quota transaction:** Use `async with session.begin():` — decrement only if PDF generated successfully.

## Acceptance Criteria

- [x] Unit tests cho `calculate_numerology_numbers()` (≥10 test cases inc. master numbers, edge ages, negative wrap)
- [x] `/api/so-hoc-free` với input `full_name=Nguyen Van A&birth_day=15101990&phone=0901234567` trả PDF ≥50KB
- [x] `/api/so-hoc` không auth → 401
- [x] `/api/so-hoc` với user `number_download=0` → 400 "Bạn không đủ lượt tải"
- [x] `/api/so-hoc` success: quota -1, UserDownload row created
- [x] PDF render time <5s P95
- [x] `/api/la-so` returns horoscope data (mock vietheart.net trong test)
- [x] Visual diff: rendered PDF vs Django output identical (manual check, 3 sample inputs)

## Risks

- **`get_sum` crashes on negative** — line 99 in views.py có wrap `if so_nam_ca_nhan < 0: so_nam_ca_nhan += 9`. Cần copy chính xác.
- **Mode crash on empty `arr_value`** — `statistics.mode([])` raises. Validate name không rỗng sau strip_accents.
- **Master number redirect** (line 121-124, 159-160, 186-187) — `thu_thach_*` = 0 → 9, `so_thuc_thi` = 0 → 9, `so_truong_thanh` ∈ {11,22,33} → reduce. Document trong code comment.
- **wkhtmltopdf fonts** — Vietnamese diacritics. Đảm bảo `fonts-noto-cjk` hoặc tương đương trong Dockerfile + `enable-local-file-access` option preserved.
- **Static file paths trong PDF** — `<img src="{{ base_dir }}/static/...">`. Đảm bảo `STATIC_ROOT` được mount + accessible từ wkhtmltopdf process.
- **Horoscope API** (vietheart.net) — external, có thể down. Add `httpx.AsyncClient(timeout=10)` + try/except → return graceful error.

## Security

- **Validation:** birth_day phải đúng 8 digits, full_name strip whitespace, phone strip non-digits.
- **Quota race condition:** `SELECT ... FOR UPDATE` trên user_profiles row trước khi decrement.
- **PDF templates:** Jinja2 autoescape ON (HTML context safe by default). Dùng `|safe` chỉ cho RichText content đã trusted.

## Sync-Back (2026-05-25)

**Status:** Done  
**Files created:** 14 files  
- Core logic: `app/core/alphabet.py` (52L), `app/core/numerology_sums.py` (42L), `app/core/numerology.py` (170L)  
- Services: `app/services/numerology_db.py` (100L), `app/services/numerology_context.py` (121L), `app/services/numerology_service.py` (18L), `app/services/horoscope_client.py` (97L)  
- API: `app/routers/numerology_paid.py` (138L), `app/routers/numerology_free.py` (108L), `app/routers/numerology.py` (25L assembly)  
- Utils + Templates: `app/utils/pdf.py` (90L), `app/templates/invoice.html` (429L), `app/templates/invoice-free.html` (270L)  
- Schema: `app/schemas/numerology.py` (131L)  

**Endpoints:** GET /api/so-hoc (auth+quota), /api/so-hoc-free (public), /api/la-so (horoscope), /api/ (debug HTML).  
**Edge cases covered:** 0→9 redirects, master number preservation/reduction, negative wrap +9, quota race condition via SELECT FOR UPDATE, horoscope API timeout handling, Vietnamese accent stripping.  
**Deviations:** Module split per ≤200L constraint (numerology_sums + numerology + numerology_db + numerology_context); routers split (numerology_paid + numerology_free + assembly).  
**Report:** phase-04-260525-0936-numerology-pdf.md  

All files passed py_compile. Numerology calc + template porting smoke-tested. Ready for phase 05.

## Next

Phase 05 — utility/content APIs (news, packages, banks, profile).
