# Numerology API

FastAPI + PostgreSQL 16 backend for the Numerology application.

## Quick Start

```bash
# 1. Copy env file and fill in secrets
cp .env.example .env

# 2. Start services (API + Postgres)
docker compose up -d

# 3. Run migrations
docker compose exec api alembic upgrade head

# 4. Verify health
curl http://localhost:8000/health
# → {"status":"ok"}

# 5. Browse API docs
open http://localhost:8000/docs
```

## Development (local, no Docker)

```bash
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

## Project Structure

```
app/
├── main.py          # FastAPI factory, CORS, /health
├── config.py        # pydantic-settings (reads .env)
├── deps.py          # DI: get_db, get_current_user (phase 03)
├── db/
│   ├── base.py      # DeclarativeBase
│   ├── session.py   # async engine + session factory
│   └── models/      # ORM models (phase 02)
├── routers/         # APIRouter per resource (phase 03+)
├── schemas/         # Pydantic v2 schemas
├── services/        # Business logic
├── core/            # security.py, oauth.py, numerology.py
├── utils/           # pdf.py render helper
└── templates/       # Jinja2 HTML templates
alembic/             # Migrations
tests/               # pytest-asyncio test suite
```

## Migrations

```bash
# Generate a new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback one step
alembic downgrade -1
```

## Seeding

After applying migrations, seed the database with placeholder content and sample data:

```bash
# Seed all tables (content + packages + banks) — idempotent, safe to re-run
docker compose exec api python -m scripts.seed_all

# Create a superuser (required for /admin/* access)
docker compose exec api python -m scripts.create_superuser \
  --email admin@example.com \
  --password Admin123! \
  --first-name Admin \
  --last-name User

# Update an existing superuser's password / details
docker compose exec api python -m scripts.create_superuser \
  --email admin@example.com \
  --password NewPass456! \
  --force

# Run individual seed scripts
docker compose exec api python -m scripts.seed_content
docker compose exec api python -m scripts.seed_packages
docker compose exec api python -m scripts.seed_banks
```

### Seed data summary

| Script | Tables seeded | Rows (approx) |
|--------|--------------|---------------|
| `seed_content.py` | 22 numerology content tables | ~393 placeholder rows |
| `seed_packages.py` | `packages` | 3 (Free / Basic / Premium) |
| `seed_banks.py` | `banks` | 1 (Vietcombank) |
| `create_superuser.py` | `users` + `user_profiles` | 1 superuser |

> Placeholder content must be replaced via the admin UI before production use.

## Production Deployment

Production artifacts live in [`deploy/`](./deploy/README.md):

| Artifact | Description |
|----------|-------------|
| `deploy/docker-compose.prod.yml` | Production stack (api + db + nginx, gunicorn, no dev ports) |
| `deploy/nginx.conf` | SSL termination, gzip, static/media, reverse proxy |
| `deploy/env.prod.example` | Env template — copy to `.env.prod`, fill secrets |
| `deploy/deploy.sh` | One-command deploy: pull → build → migrate → restart |
| `deploy/backup.sh` | Daily Postgres dump cron script (14-day rotation) |
| `deploy/cutover.md` | Cutover runbook: Django → FastAPI (~30min downtime) |
| `deploy/rollback.md` | Rollback runbook if cutover fails (< 10min recovery) |

See **[deploy/README.md](./deploy/README.md)** for first-time setup order and subsequent deploy instructions.
