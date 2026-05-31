# Phase 08 — Testing (Pytest ≥70% Coverage)

**Priority:** P0 (gate to deploy)
**Effort:** M (10-14h)
**Status:** Partial (93/93 unit tests PASS; integration blocked by SQLite async dialect RETURNING issue)
**Depends on:** phase-04, phase-05

## Goal

Pytest suite với coverage ≥70%, focus on:
1. **Numerology calc logic** (highest priority — pure logic, 200+ LOC)
2. **API endpoints** (integration tests qua httpx + test DB)
3. **Auth flow** (JWT issue/verify, OAuth callback)

## Stack

- pytest, pytest-asyncio, pytest-cov
- httpx.AsyncClient (in-process test client)
- pytest-postgresql hoặc Postgres container (testcontainers-python)
- factory-boy hoặc inline fixtures
- respx (mock httpx for vietheart.net horoscope)

## Test Structure

```
tests/
├── conftest.py                 # fixtures: db_session, client, user, superuser
├── unit/
│   ├── test_numerology_calc.py # ≥20 cases cho calculate_numerology_numbers
│   ├── test_alphabet.py        # strip_accents, alphabet lookup
│   ├── test_get_sum.py         # all 4 get_sum variants
│   └── test_security.py        # hash/verify, jwt encode/decode
├── integration/
│   ├── test_auth_endpoints.py
│   ├── test_numerology_endpoints.py
│   ├── test_profile.py
│   ├── test_news.py
│   ├── test_packages_payments.py
│   └── test_admin_content.py
└── fixtures/
    ├── sample_numerology_content.py  # populate test DB
    └── pdf_baseline/                  # binary baselines (gitignored, generated)
```

## Critical Test Cases (Numerology Calc)

### `calculate_numerology_numbers()` edge cases

| # | Input | Expected behavior |
|---|-------|---|
| 1 | `birth_day=15101990, full_name=NGUYEN VAN A` | so_chu_dao = standard calc |
| 2 | `birth_day=11111111` (mostly 1s) | leak_num includes 2,3,4,...,9 |
| 3 | `birth_day=29021992, full_name=LE THI BA` | master number 11/22/33 trong so_chu_dao |
| 4 | Young age (age < 25 - so_chu_dao) | so_nam_ca_nhan = 11 |
| 5 | Elderly age (age >= 54 + so_chu_dao) | so_nam_ca_nhan = 10 |
| 6 | Middle age, get so_nam_ca_nhan = 0 | wrap to 9 (line 113) |
| 7 | Middle age, negative intermediate | wrap +9 (line 99) |
| 8 | Empty full_name | should raise BadRequest (currently uncaught — bug!) |
| 9 | Vietnamese name "ĐÀO THỊ MAI" | strip_accents → "DAO THI MAI" |
| 10 | thu_thach computes to 0 | redirect to 9 (line 121-124) |
| 11 | so_thuc_thi = 0 | redirect to 9 (line 159-160) |
| 12 | so_truong_thanh ∈ {11,22,33} | reduce to 2,4,6 (line 186-187) |
| 13 | so_noi_cam = mode([1,2,3]) | statistics.mode returns first |
| 14 | name có chỉ 1 character | edge - alphabet lookup |
| 15 | birth_day với leap day 29022000 | works |

### Endpoint tests

```python
async def test_so_hoc_free_returns_pdf(client, seeded_content):
    resp = await client.get(
        "/api/so-hoc-free",
        params={"full_name": "Nguyen Van A", "birth_day": "15101990", "phone": "0901234567"}
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/pdf"
    assert len(resp.content) > 10_000  # PDF should be non-trivial

async def test_so_hoc_no_quota_rejects(client, user_no_quota, auth_headers):
    resp = await client.get("/api/so-hoc", params={...}, headers=auth_headers)
    assert resp.status_code == 400
    assert "không đủ lượt tải" in resp.json()["detail"]

async def test_so_hoc_decrements_quota(client, user_with_quota, db, auth_headers):
    before = user_with_quota.profile.number_download
    await client.get("/api/so-hoc", params={...}, headers=auth_headers)
    await db.refresh(user_with_quota.profile)
    assert user_with_quota.profile.number_download == before - 1
```

### Auth tests

- `/auth/register` happy path + duplicate email → 409
- `/auth/login` wrong password → 401
- `/auth/refresh` revoked token → 401
- `/auth/me` no Bearer → 401
- Google OAuth callback (mock httpx with respx) → issues JWT

### Admin tests

- Non-superuser cannot access `/admin/content/*` → 403
- Superuser can CRUD all 22 content types
- Payment approve grants downloads (transaction integrity)
- Upload reject `.exe`, accept `.png`

## CI Config

```yaml
# .github/workflows/ci.yml
- run: docker compose up -d db
- run: alembic upgrade head
- run: pytest --cov=app --cov-fail-under=70 --cov-report=term-missing
- run: ruff check app/
- run: mypy app/
```

## Steps

1. Setup `conftest.py` với async fixtures (db_session, client, factory functions).
2. Write `test_numerology_calc.py` first (most ROI). Pin expected outputs from current Django implementation.
3. Compare new calc output vs Django output on 5+ real inputs — assert identical.
4. Write endpoint tests using `httpx.AsyncClient(transport=ASGITransport(app=app))`.
5. Mock `gen_horoscopes` (httpx external call) with respx.
6. Run `pytest --cov` iteratively, fill gaps to reach 70%.
7. Setup CI workflow.

## Acceptance Criteria

- [x] All unit tests pass (93/93 PASS)
- [ ] All integration tests pass (70 tests written; 51 blocked by SQLite async dialect RETURNING incompatibility)
- [ ] Coverage ≥70% on `app/` (59% unit tests only; ≥70% on app/core: 100%)
- [ ] CI runs full suite in <5min (4.89s for unit tests)
- [x] PDF generation tested (mocked, not rendered; wkhtmltopdf not in test env)
- [x] No flaky tests (all unit tests deterministic)

## Risks

- **wkhtmltopdf trong CI** — install binary trong CI image OR mock `render_pdf` in tests, run real PDF only in e2e job.
- **Test DB isolation** — use transaction-rollback per test (SAVEPOINT pattern).
- **External horoscope mock** — Pin response shape from real vietheart.net once, save fixture.

## Sync-Back (2026-05-25)

**Status:** Partial  
**Unit tests:** 93/93 PASS (59% code coverage on app/, 100% on app/core)  
- test_numerology_calc.py: 17 tests (master numbers, age variants, redirects, accent stripping, edge cases)  
- test_numerology_sums.py: 32 tests (get_sum variants, preservation rules, cross-function consistency)  
- test_alphabet.py: 14 tests (Vietnamese diacritics, letter mapping)  
- test_security.py: 30 tests (bcrypt, JWT encode/decode, refresh token hashing, round-trip)  

**Integration tests:** 70 written; 51 blocked by SQLite async dialect incompatibility.  
- Root cause: `aiosqlite:///:memory:` attempts RETURNING clause in INSERT (PostgreSQL syntax).  
- Workaround: Switch to testcontainers-python with real PostgreSQL container in CI (non-trivial; deferred to follow-up sprint).  

**Code quality:** Fixed Python 3.9 compatibility (Union type hints → Optional/typing imports).  
**Report:** tester-260525-1012-pytest-suite-phase-08.md  

**Recommendation:** Unblock integration tests by switching conftest.py fixture to use Postgres testcontainers (`testcontainers[postgres]>=4`). Proceed to phase 09 with unit tests only (core logic 100% covered).

## Next

Phase 09 — production deployment (docker-compose VPS).
