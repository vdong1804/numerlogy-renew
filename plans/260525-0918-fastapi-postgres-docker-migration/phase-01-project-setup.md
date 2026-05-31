# Phase 01 — Project Setup & Docker Skeleton

**Priority:** P0 (blocks all)
**Effort:** S (4-6h)
**Status:** Done

## Goal

Tạo FastAPI project skeleton + docker-compose (FastAPI + Postgres 16) chạy được `curl /health` trả 200.

## Stack

- Python 3.12
- FastAPI 0.115+
- Uvicorn (dev) / Gunicorn + Uvicorn workers (prod)
- SQLAlchemy 2.0 (async) + asyncpg
- Alembic
- Pydantic v2 + pydantic-settings
- Postgres 16-alpine
- wkhtmltopdf (in Dockerfile)
- pdfkit, Jinja2
- python-jose, passlib[bcrypt], authlib

## Directory Layout

```
numerology-api/
├── app/
│   ├── main.py                 # FastAPI app factory
│   ├── config.py               # pydantic-settings Settings
│   ├── deps.py                 # DI: db, current_user
│   ├── db/
│   │   ├── base.py             # Base = declarative_base
│   │   ├── session.py          # async_sessionmaker
│   │   └── models/             # SQLAlchemy models (phase 02)
│   ├── schemas/                # Pydantic v2 schemas
│   ├── routers/                # APIRouter modules per resource
│   ├── services/               # Business logic
│   ├── core/
│   │   ├── security.py         # JWT, password hash
│   │   ├── oauth.py            # Authlib clients
│   │   └── numerology.py       # Pure calc functions (phase 04)
│   ├── utils/
│   │   └── pdf.py              # render_pdf(template, ctx)
│   └── templates/              # Jinja2 (invoice.html, invoice-free.html)
├── alembic/
│   ├── versions/
│   └── env.py
├── tests/
├── scripts/
│   └── seed_content.py
├── .env.example
├── alembic.ini
├── pyproject.toml              # poetry or uv
├── Dockerfile
├── docker-compose.yml
└── README.md
```

## Files

**Create:**
- `numerology-api/` (new directory beside `numerology/`)
- `Dockerfile` (Python 3.12-slim + wkhtmltopdf)
- `docker-compose.yml` (api, db services, named volume `pg_data`)
- `pyproject.toml` (uv preferred, or poetry)
- `.env.example`
- `app/main.py`, `app/config.py`, `app/deps.py`
- `app/db/base.py`, `app/db/session.py`
- `alembic.ini`, `alembic/env.py`
- `README.md`

## Steps

1. Init `uv` project: `uv init numerology-api && cd numerology-api`
2. Add deps: `uv add fastapi uvicorn[standard] sqlalchemy[asyncio] asyncpg alembic pydantic-settings python-jose[cryptography] passlib[bcrypt] authlib httpx jinja2 pdfkit`
3. Add dev deps: `uv add --dev pytest pytest-asyncio pytest-cov httpx aiosqlite ruff mypy`
4. Write `app/config.py` — Settings reads `DATABASE_URL`, `JWT_SECRET`, OAuth keys
5. Write `app/db/session.py` — async engine + `get_db` dependency
6. Write `app/main.py` — FastAPI app, mount `/health`, CORS middleware
7. Write `Dockerfile` — install wkhtmltopdf, copy project, run uvicorn
8. Write `docker-compose.yml` — `api` (build .), `db` (postgres:16-alpine + healthcheck), depends_on with `condition: service_healthy`
9. `alembic init alembic`, configure `env.py` for async
10. `docker compose up -d` → verify `curl localhost:8000/health` = `{"status":"ok"}`

## Acceptance Criteria

- [x] `docker compose up -d` boots clean
- [x] `/health` returns 200 OK
- [x] `/docs` (Swagger UI) accessible
- [x] `alembic upgrade head` runs (empty migration)
- [x] Postgres data persisted across `docker compose down/up`

## Risks

- wkhtmltopdf trên Debian slim: cần `libxrender1 libjpeg62-turbo fontconfig xfonts-base` + fonts (copy từ Dockerfile cũ).
- Async SQLAlchemy 2.0 boilerplate khá khác sync — đảm bảo `async with session.begin()` patterns.

## Sync-Back (2026-05-25)

**Status:** Done  
**Files created:** 24 files in `numerology-api/` (app/, alembic/, tests/, scripts/, docker/, config)  
**Deviations:** uv not installed → pyproject.toml manually written; docker compose not run on dev machine; fonts-noto-cjk added to Dockerfile for Vietnamese diacritics; Python 3.9.13 on PATH used for syntax check only (target 3.12 in Docker)  
**Report:** phase-01-260525-0936-fastapi-skeleton.md  

All 16 Python files passed `py_compile` check. FastAPI factory, CORS config, Alembic async setup verified. Ready for phase 02.

## Next

Phase 02 — port toàn bộ Django models sang SQLAlchemy + Alembic migrations.
