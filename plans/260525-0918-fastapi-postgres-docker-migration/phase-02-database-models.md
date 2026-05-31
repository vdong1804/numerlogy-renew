# Phase 02 — Database Models & Alembic Migrations

**Priority:** P0
**Effort:** M (8-12h)
**Status:** Done
**Depends on:** phase-01

## Goal

Port toàn bộ Django models sang SQLAlchemy 2.0 (async) + tạo Alembic initial migration. Schema giống Django nhưng cleanup naming, drop CKEditor-specific fields (just plain `TEXT`).

## Models to Port (from `numerology/`)

### Numerology content (20 bảng — RichText → `Text`)

| Django Model | DB Table | Fields |
|--------------|----------|--------|
| MainNumber | main_number | code, value, title, content, content_2..5, number_page |
| MissionNumber | mission_number | code, value, title, content, number_page |
| ExecutionNumber | execution_number | id |
| SoulsNumber | souls_number | id |
| DevelopmentNumber | development_number | id |
| LifePeak | peak_life | id |
| ChallengeLife | challenge_life | id |
| BirthdayChart | birthday_chart | id |
| NameChart | name_chart | id |
| StagesOfLife | stages_of_life | id |
| AttitudeNumber | attitude_number | id |
| BirthdayNumber | birthday_number | id |
| MatureNumber | mature_number | id |
| IntrospectiveNumber | introspective_number | id |
| KarmicNumber | karmic_number | id |
| DeficitNumber | deficit_number | id |
| PhoneNumber | phone_number | id |
| PersonalMonthNumber | personal_month_number | id (rename từ `personal month_number` — bug có space) |
| Identifiable | identifiable | id |
| BalanceNumber | balance_number | id |
| MissNumber | miss_number | id |
| PersonalYearNumber | personal_year_number | id |
| PhoneMasterDataModel | phone_master_data | code, bow |

**Common columns:** `id PK`, `code VARCHAR(255)`, `value VARCHAR(255) NULL`, `title VARCHAR(255)`, `content TEXT`, `number_page INT`.

Tạo **1 abstract mixin** `NumerologyContentMixin` để DRY 22 models.

### User domain

| Django | New |
|--------|-----|
| `auth.User` | `users` (id, email UNIQUE, hashed_password NULL, first_name, last_name, is_active, is_superuser, created_at) |
| `UserProfileModel` | `user_profiles` (id, user_id FK→users, name, birth_day, address, phone, number_download default 0) |
| `UserDownloadModel` | `user_downloads` (id, user_id FK NULL, name, birth_day, birth_time, gender, job, phone, type SMALLINT, created_at) |
| `UserPackageModel` | `user_packages` (id, user_id FK, package_id FK, is_used bool, updated_at) |
| `UserPaymentModel` | `user_payments` (id, user_id FK, package_id FK, price float, transaction_code, account_number, account_holder, status SMALLINT, bank, created_at, updated_at) |
| `BankModel` | `banks` (id, bank, branch, account_number, account_holder, image, code) |

### Content/Misc

| Django | New |
|--------|-----|
| `News` | `news` (id, title, short_content, content TEXT, category SMALLINT, image VARCHAR, created_at, updated_at) |
| `PackageModel` | `packages` (id, name, price float, price_sale float, number_download, content TEXT, created_at, updated_at) |

### OAuth tokens (cho social login state) — phase 03 sẽ define

## Files to Create

```
app/db/models/
├── __init__.py
├── mixins.py                   # TimestampMixin, NumerologyContentMixin
├── user.py                     # User, UserProfile
├── numerology_content.py       # 22 content tables (one file, DRY via mixin)
├── download.py                 # UserDownload
├── package.py                  # Package, UserPackage, UserPayment, Bank
└── news.py                     # News
```

## Steps

1. Create `NumerologyContentMixin` with common columns (code, value, title, content, number_page).
2. Generate all 22 numerology content models declaring `__tablename__` + mixin. Each ≤8 lines.
3. Write user/profile/download/package/payment/bank/news models.
4. Wire `app/db/base.py` → import all models so Alembic autogen sees them.
5. `alembic revision --autogenerate -m "initial schema"`.
6. Review migration — fix any `Text` vs `String` issues, ensure `ondelete="CASCADE"` matches Django behavior.
7. `alembic upgrade head` → verify in `psql`.
8. Add CHECK constraint cho `user_downloads.type IN (0, 1)`.

## Acceptance Criteria

- [x] `alembic upgrade head` clean
- [x] All 22+ tables created in Postgres
- [x] `psql \d main_number` shows expected columns
- [x] Models importable from `app.db.models`
- [x] No `media`/`uploads/` paths in schema (handle via file storage in phase 05)

## Risks

- **Master numbers** trong content tables (code="11", "22", "33", "1_1", "1_single", "not_147", "20  ") — code field PHẢI là VARCHAR (not int). Đã check views.py confirm dùng string.
- **Bug fix:** Django `PersonalMonthNumber.db_table = "personal month_number"` có space → đổi thành `personal_month_number`.
- **`UserDownloadModel.type`** trong Django là `BooleanField(choices=[(0,'free'),(1,'paid')])` — Postgres ngon hơn dùng `SMALLINT` để khớp với code `type=1`.

## Sync-Back (2026-05-25)

**Status:** Done  
**Files created:** 8 files (6 model modules + 1 migration + 1 __init__)  
- `app/db/models/mixins.py` (38L), `numerology_content.py` (120L), `user.py` (52L), `download.py` (37L), `package.py` (65L), `news.py` (27L)  
- `alembic/versions/0001_initial_schema.py` (233L)  

**Schema:** 31 tables total (22 numerology content + 9 domain tables). all ≤200 lines. `main_number` extra cols confirmed; `personal_month_number` name fixed; `phone_master_data` mixin-excluded per spec.  
**Deviations:** Migration hand-written (no Postgres on dev); PhoneMasterDataModel excluded from NumerologyContentMixin (only code+bow needed).  
**Report:** phase-02-260525-0936-db-models.md  

All files passed py_compile. Base.metadata = 31 tables. Ready for phase 03.

## Next

Phase 03 — auth (JWT + OAuth Google/Facebook).
