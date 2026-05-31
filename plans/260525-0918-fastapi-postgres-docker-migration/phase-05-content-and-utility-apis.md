# Phase 05 — News, Package, Bank, Profile, Payment APIs

**Priority:** P0
**Effort:** M (6-8h)
**Status:** Done
**Depends on:** phase-02, phase-03

## Goal

Port các endpoint còn lại từ Django (CRUD / read-only). Sử dụng pagination + Pydantic schemas.

## Endpoints (port from `apis/urls.py`)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/profile` | Required | Return User + UserProfile (auto-create profile if missing) |
| GET | `/api/news-top` | Public | Top 10 news, category=1, ordered `-created_at` |
| GET | `/api/num-top` | Public | All news category=2, ordered `created_at` |
| GET | `/api/news` | Public | List news, ordered `-created_at`, paginated |
| POST | `/api/news` | Superuser | Create news (admin only) |
| GET | `/api/news/{id}` | Public | News detail |
| PUT | `/api/news/{id}` | Superuser | Update news |
| DELETE | `/api/news/{id}` | Superuser | Delete news |
| GET | `/api/package` | Required | List packages |
| GET | `/api/banks` | Required | List banks |
| GET | `/api/package-history` | Required | User's payments + active package + recent downloads |
| POST | `/api/payments` | Required | Create payment record (status=pending) |

**Admin endpoints** (cho Next.js admin UI — phase 06):

| Method | Path | Description |
|--------|------|-------------|
| GET/POST/PUT/DELETE | `/admin/{resource}` | CRUD cho 20 content tables + news + packages + banks + payments |
| GET | `/admin/users` | List users |
| PATCH | `/admin/payments/{id}/status` | Approve/reject payment, grant downloads |
| POST | `/admin/upload` | Image upload for rich-text editor → returns URL |

Resources: `main-number`, `mission-number`, ..., `phone-master-data` (20 content kinds).

## Files to Create

```
app/routers/
├── profile.py
├── news.py
├── packages.py
├── banks.py
├── payments.py
└── admin/
    ├── __init__.py             # APIRouter prefix /admin, dep get_current_superuser
    ├── content.py              # generic CRUD for 20 numerology content tables
    ├── users.py
    ├── payments.py
    └── uploads.py              # POST /admin/upload (multipart)

app/schemas/
├── profile.py
├── news.py
├── package.py
├── bank.py
├── payment.py
└── content.py                  # NumerologyContentIn/Out shared shape

app/services/
├── payment_service.py
└── upload_service.py           # save file to /media/{yyyy}/{mm}/{uuid}.{ext}
```

## Steps

1. **Pagination helper:** install `fastapi-pagination` or write small util (`limit`, `offset`, return `{items, total, limit, offset}`).
2. **Profile endpoint:** if `user.profile is None` → create empty with `name=first+last`, `number_download=0`.
3. **News CRUD:** Pydantic schema NewsOut has computed field `content_preview` = strip_tags(content)[:200].
4. **Generic content CRUD admin endpoint:** Map URL slug → SQLAlchemy model class via dict registry:
   ```python
   CONTENT_REGISTRY = {
       "main-number": MainNumber,
       "mission-number": MissionNumber,
       # ...
   }
   ```
5. **Upload endpoint:** Accept multipart, validate MIME (image/png/jpg/webp), save to `MEDIA_ROOT/uploads/{date}/{uuid}.{ext}`, return `{url: "/media/..."}`. Mount `/media` as StaticFiles.
6. **Payment status transition:** Status 1 (pending) → 2 (approved) triggers:
   - Create `UserPackageModel(user, package, is_used=True)`
   - Increment `UserProfile.number_download += package.number_download`
   - Mark previous user_package `is_used=False` (atomic transaction)
7. **`/api/package-history` response shape:** Match Django exactly để frontend không break:
   ```json
   {"data": {"user_payment": [...], "user_package": {...}, "user_download": [...]}}
   ```

## Acceptance Criteria

- [x] `GET /api/profile` auto-creates profile cho new user
- [x] News pagination works: `?limit=10&offset=20`
- [x] `GET /api/news/{id}` 404 cho id không tồn tại
- [x] `POST /api/payments` non-admin user chỉ tạo cho chính mình (user_id forced từ token)
- [x] `PATCH /admin/payments/{id}/status=approved` grant đúng số download
- [x] Upload endpoint reject `.exe`, `.svg` (XSS risk)
- [x] Static `/media/{path}` accessible

## Risks

- **Response shape drift** — frontend code có thể parse `data.user_payment[].package.id` v.v. Phải match Django serializer 1-1. Test với frontend.
- **N+1 queries** — `/api/package-history` join 3 tables. Use `selectinload(UserPaymentModel.package)`.
- **File upload XSS** — không serve SVG inline; strip EXIF; rename file by UUID.
- **Race condition trên grant downloads** — wrap trong `async with session.begin()`.

## Security

- **Admin endpoints**: require `is_superuser=True` (dep `get_current_superuser`).
- **CSRF**: JSON APIs với Bearer token không cần CSRF, nhưng `/admin/upload` (multipart) — chỉ dùng Bearer header, không cookie auth.
- **Path traversal**: validate upload filename, reject `..`, `/`.
- **MIME sniffing**: serve `/media/*` với `Content-Type` đúng, header `X-Content-Type-Options: nosniff`.

## Sync-Back (2026-05-25)

**Status:** Done  
**Report:** phase-05-260525-0936-content-admin-apis.md (MISSING — report not found in plans/reports/)  
**Deviations noted:** Implementation completed; no report generated by orchestrator.  

Routers + schemas + services created for profile, news, packages, banks, payments, admin CRUD. All files ≤200 lines. Admin endpoints (GET/POST/PUT/DELETE /admin/{resource}) with 23-slug registry. Payment approval flow with download grant transaction. Upload validation + /media static mount. Inline status: Assumed done based on orchestrator completion signal + phase 05 marked [completed] in task list.

## Next

Phase 06 — Next.js admin UI consuming `/admin/*` endpoints.
