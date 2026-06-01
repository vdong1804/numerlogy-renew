# Deployment Guide

**Version:** 1.1  
**Last Updated:** 2026-05-26  
**Target:** Single VPS with Docker Compose

---

## Quick Reference

**Production Deployment One-Liner:**
```bash
cd /path/to/numerology-api/deploy && bash deploy.sh
```

**Full Rollback (if deployment fails):**
```bash
cd /path/to/numerology-api/deploy && bash rollback.sh
```

---

## Local Development Setup

### Prerequisites
- Docker + Docker Compose installed
- Python 3.12 + pip
- Node.js 18+ + npm
- wkhtmltopdf installed (`brew install wkhtmltopdf` on macOS, `apt-get install wkhtmltopdf` on Linux)

### Backend (FastAPI)

```bash
cd numerology-api

# 1. Copy env template and fill secrets
cp .env.example .env
# Edit .env with local values

# 2. Start Docker stack (PostgreSQL + API)
docker compose up -d

# 3. Run database migrations
docker compose exec api alembic upgrade head

# 4. Seed database
docker compose exec api python -m scripts.seed_all

# 5. Create superuser (for admin access)
docker compose exec api python -m scripts.create_superuser \
  --email admin@example.com \
  --password Admin123! \
  --first-name Admin \
  --last-name User

# 6. Verify health
curl http://localhost:8000/health
# → {"status":"ok"}

# 7. Browse API docs
open http://localhost:8000/docs
```

### Frontend (Next.js)

```bash
cd Numerology-Landing-Page

# 1. Copy env template
cp .env.example .env.local
# Edit with API_BASE=http://localhost:8000

# 2. Install dependencies
npm install

# 3. Start dev server
npm run dev

# 4. Open browser
open http://localhost:3000
```

### Database Migrations (Local Development)

```bash
cd numerology-api

# Generate new migration after model change
docker compose exec api alembic revision --autogenerate -m "description"

# Apply pending migrations
docker compose exec api alembic upgrade head

# Rollback one step
docker compose exec api alembic downgrade -1

# View migration history
docker compose exec api alembic history
```

**Migration 0012 (Phase 05 — Chat Addons):**
- Introduces `chat_addon_purchases` table (user_id, package_id, addon_id PK, payment_id UNIQUE, remaining_messages, expires_at)
- Adds `packages` columns: `package_kind` (enum: pdf_download|chat_addon), `message_count`, `tier`, `validity_days`
- Partial index on `chat_addon_purchases(user_id, expires_at)` for cleanup queries
- **Action on deploy:** Ensure `alembic upgrade head` runs before restarting API service

**Migration 0013 (Phase 06 — Semantic Cache + Rate Limit):**
- Introduces 2 new tables: `semantic_cache_entries`, `rate_limit_buckets`
- Creates HNSW cosine index on `semantic_cache_entries.embedding` (requires **pgvector ≥0.5.0**)
- **CRITICAL:** Ensure `pgvector >= 0.5.0` installed before running migration. Verify:
  ```bash
  docker compose -f docker-compose.prod.yml exec postgres psql -U numerology -d numerology \
    -c "SELECT extversion FROM pg_extension WHERE extname='vector';"
  # Expected: 0.5.0 or later
  ```
- **Action on deploy:** Ensure `alembic upgrade head` runs before restarting API service
- **Background job:** `cleanup_semantic_cache` scheduler entry added (nightly 03:15 UTC) — deletes expired semantic cache entries. No manual config required.

**Migration a1d6e2c84f31 (DeepSeek LLM Migration, 2026-06-01):**
- Drops `prompt_cache_handles` table (ephemeral cache, no data loss)
- Removes Gemini flash/pro model support; all chat LLM now routes to DeepSeek (`deepseek-chat`)
- Embeddings unchanged (Gemini `text-embedding-004` retained)
- **Action on deploy:** Ensure `alembic upgrade head` runs. No config migration needed (see `.env.example` for new DeepSeek vars).

---

## Production Deployment

### Initial Setup (One-Time)

**1. Prepare VPS:**
- Ubuntu 22.04 LTS (or similar)
- 2-4 vCPU, 4GB+ RAM
- SSH access, sudo privileges
- Docker + Docker Compose pre-installed

**2. Clone repository:**
```bash
ssh root@vps-ip
cd /opt
git clone https://github.com/your-org/numerology.git
cd numerology/numerology-api
```

**3. Create production env:**
```bash
cp deploy/env.prod.example .env.prod
# Edit .env.prod with production secrets:
# - DATABASE_URL (strong Postgres password)
# - JWT_SECRET (strong random string, e.g., `openssl rand -hex 32`)
# - Google/Facebook OAuth credentials (from console.cloud.google.com)
# - FRONTEND_URL (production domain)
# - CORS_ORIGINS (production domain)
```

**4. Set up SSL certificates (Certbot):**
```bash
# Create certbot webroot directory
mkdir -p /var/www/certbot

# Initial certificate request
certbot certonly --webroot -w /var/www/certbot \
  -d nhansinhquan.vn -d api.nhansinhquan.vn \
  --email admin@nhansinhquan.vn --agree-tos --non-interactive

# Update nginx.conf ssl_certificate paths if needed
```

**5. Deploy and start services:**
```bash
cd /opt/numerology/numerology-api/deploy
bash deploy.sh
```

**6. Set up automated backups:**
```bash
# Copy backup script
cp backup.sh /opt/numerology/numerology-api/deploy/

# Add to crontab (daily at 2 AM)
crontab -e
# Add: 0 2 * * * bash /opt/numerology/numerology-api/deploy/backup.sh

# Set up cert renewal hook (in Certbot config)
echo "post_hook = systemctl reload nginx" >> /etc/letsencrypt/renewal/nhansinhquan.vn.conf
```

### Subsequent Deployments

**After code changes:**
```bash
cd /opt/numerology/numerology-api/deploy

# Pull latest code
git pull origin main

# Deploy (auto: build → migrate → restart)
bash deploy.sh
```

**Verify deployment:**
```bash
# Check container status
docker compose -f docker-compose.prod.yml ps

# Check logs
docker compose -f docker-compose.prod.yml logs -f api

# Health check
curl https://api.nhansinhquan.vn/health
# → {"status":"ok"}
```

### Nginx SSE Configuration (Chat Streaming — Phase 04)

Streaming chat endpoint requires HTTP/1.1 keepalive + no buffering. Nginx config includes dedicated location:

**Location Regex (deploy/nginx.conf, line ~120):**
```nginx
location ~ ^/api/chat/conversations/\d+/messages/stream$ {
  proxy_pass http://api:8000;
  proxy_buffering off;
  proxy_request_buffering off;
  gzip off;
  proxy_read_timeout 300s;
  proxy_set_header X-Accel-Buffering no;
}
```

**Key Directives:**
- `proxy_buffering off` — nginx does not buffer response body; forward chunks immediately
- `proxy_request_buffering off` — client sends request body without buffering  
- `gzip off` — disable compression (SSE frames must be sent raw)
- `proxy_read_timeout 300s` — allow 5-minute stream (covers slow LLM calls)
- `X-Accel-Buffering: no` — tells FastAPI to not proxy-buffer (redundant but explicit)

**Client Contract:**
- HTTP/1.1 persistent connection (automatic in modern browsers)
- Bearer JWT in `Authorization` header
- Expect `Content-Type: text/event-stream`
- Frames delimited by `\n\n`; parse with `TextDecoder({ stream: true })`

---

## Environment Variables Reference

### Backend (numerology-api/.env or .env.prod)

| Variable | Example | Required | Notes |
|----------|---------|----------|-------|
| `DATABASE_URL` | `postgresql+asyncpg://user:pass@localhost:5432/numerology` | Yes | Postgres async driver |
| `JWT_SECRET` | `openssl rand -hex 32` | Yes | >32 chars, random |
| `JWT_ALGORITHM` | `HS256` | Yes | Fixed |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `15` | Yes | JWT validity |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` | Yes | Refresh token validity |
| `GOOGLE_CLIENT_ID` | `...apps.googleusercontent.com` | Yes | From Google Cloud Console |
| `GOOGLE_CLIENT_SECRET` | `GOCSP...` | Yes | From Google Cloud Console |
| `FACEBOOK_APP_ID` | `123456789` | Yes | From Facebook Developers |
| `FACEBOOK_APP_SECRET` | `abc123xyz...` | Yes | From Facebook Developers |
| `FRONTEND_URL` | `http://localhost:3000` (dev) or `https://nhansinhquan.vn` (prod) | Yes | For OAuth redirect |
| `OAUTH_REDIRECT_BASE` | `http://localhost:8000` (dev) or `https://api.nhansinhquan.vn` (prod) | Yes | For OAuth callback |
| `CORS_ORIGINS` | `["http://localhost:3000"]` (dev) or `["https://nhansinhquan.vn"]` (prod) | Yes | JSON array |
| `WKHTMLTOPDF_CMD` | `/usr/bin/wkhtmltopdf` | No | Default; override if non-standard |
| `ENVIRONMENT` | `development` or `production` | No | Used for logging level |
| `DEBUG` | `True` (dev) or `False` (prod) | No | FastAPI debug mode |
| `LOG_LEVEL` | `INFO` or `DEBUG` | No | Logging level |
| `DATABASE_POOL_SIZE` | `20` | No | SQLAlchemy connection pool |

### Frontend (Numerology-Landing-Page/.env.local or deployment config)

| Variable | Example | Required | Notes |
|----------|---------|----------|-------|
| `NEXT_PUBLIC_API_BASE` | `http://localhost:8000` (dev) or `https://api.nhansinhquan.vn` (prod) | Yes | Must start with http/https |

### Gemini API Setup (Chatbot RAG Foundation — Phase 01)

**Overview:** Knowledge base ingestion, embedding, and quotas require Google Gemini API credentials.

**1. Create Gemini API Key**

1. Open https://aistudio.google.com/apikey (requires Google account)
2. Click "Create API Key" → new project or select existing
3. Copy key (looks like `AIzaXxX...`); save securely
4. Keep page open to enable APIs below

**2. Enable Required APIs**

In Google Cloud Console (https://console.cloud.google.com):
1. Project: Select project matching API key
2. APIs & Services → Enable APIs → Search + enable:
   - `Generative Language API` (for `text-embedding-004` embedding model)

**3. Add to Environment**

```bash
# .env (local dev) or .env.prod (production)
# Embeddings (Gemini)
GEMINI_API_KEY=AIzaXxX...
EMBEDDING_MODEL=text-embedding-004          # Fixed model (required)
EMBEDDING_BATCH_SIZE=100                    # Texts per API call (default 100, max ~200)

# Chat LLM (DeepSeek)
DEEPSEEK_API_KEY=sk_...
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_CHAT_MODEL=deepseek-chat

# Chunking
CHUNK_MAX_TOKENS=500                        # Chunk window size (default 500)
CHUNK_OVERLAP_TOKENS=50                     # Overlap between chunks (default 50)
```

**4. Use a Postgres image that includes pgvector**

Migration 0010 runs `CREATE EXTENSION vector`, which requires the extension to
be **installed on the host server**. Plain `postgres:16-alpine` does NOT
include it. Use `pgvector/pgvector:pg16` (same volume layout, drop-in
replacement). The repo `docker-compose.yml` is already set to this image.

```yaml
# numerology-api/docker-compose.yml
services:
  db:
    image: pgvector/pgvector:pg16
```

For managed cloud Postgres (RDS, CloudSQL, Supabase), pgvector must be enabled
through the provider's extension list — verify before running the migration.

**5. Apply Database Migration**

```bash
# Local dev
docker compose exec api alembic upgrade head

# Production
docker compose -f docker-compose.prod.yml exec api alembic upgrade head
```

Migration `0010_chatbot_foundation.py` will:
- Install pgvector extension (one-time, via `CREATE EXTENSION IF NOT EXISTS vector`)
- Create 5 tables: kb_documents, kb_chunks, chat_conversations, chat_messages, chat_quota_usage
- Create HNSW cosine index on kb_chunks.embedding (768-dim)

Verify after upgrade:
```bash
docker compose exec db psql -U numerology -d numerology \
  -c "SELECT extname, extversion FROM pg_extension WHERE extname='vector';"
# Expected: vector | 0.8.x
```

**6. Backfill Knowledge Base (Optional)**

Script: `scripts/backfill_kb.py` — ingests numerology content into KB (one KB document per numerology content record, atomically chunked + embedded).

```bash
# Local dev — dry run (preview, no DB changes)
docker compose exec api python -m scripts.backfill_kb --dry-run
# Output: [INFO] Would ingest 40 documents from 5 numerology tables

# Local dev — real run (embeds + inserts chunks)
docker compose exec api python -m scripts.backfill_kb
# Takes ~2-5 min depending on content volume + API rate limits

# Production
docker compose -f docker-compose.prod.yml exec api python -m scripts.backfill_kb --dry-run
docker compose -f docker-compose.prod.yml exec api python -m scripts.backfill_kb
```

**Note:** Backfill is idempotent; re-running upserts existing documents (re-embeds chunks if model version changes).

**7. Listener Registration (Automatic)**

On app startup, if `GEMINI_API_KEY` is set:
- SQLAlchemy event listeners register for numerology content CRUD (insert/update/delete)
- Asyncio worker queue starts in lifespan
- New content automatically ingests to KB within seconds

**Disable for bulk seeding:** During `scripts/seed_content.py` runs, listener may trigger on every row (slow + wasteful). Workaround: comment out `register_kb_sync_listeners()` call in `app/main.py` lifespan, then re-run backfill after seeding.

### Chatbot RAG Chat API Setup (Phase 02)

**Overview:** Chat endpoints (retrieval + LLM generation + citations) require additional config beyond Phase 01 KB foundation.

**1. Add New Config Variables**

```bash
# .env (local dev) or .env.prod (production)
# Retrieval
RAG_TOP_K_FREE=3              # Free-tier chunks per query
RAG_TOP_K_PAID=8              # Paid-tier chunks per query
RAG_SIM_THRESHOLD=0.6         # Cosine similarity floor (0.0–1.0)

# Chat history
HISTORY_MAX_MESSAGES=5        # Prior turns to include in prompt

# LLM timeout
LLM_TIMEOUT_SECONDS=30        # Gemini API call hard stop
```

**2. Deploy Chat Endpoints**

Migration 0011 (auto-applied) creates `chat_conversations` and `chat_messages` tables if not present.

Endpoints available at:
- `POST /api/chat/conversations` — Create new conversation
- `GET /api/chat/conversations` — List user's conversations
- `GET /api/chat/conversations/{id}` — Get conversation detail
- `DELETE /api/chat/conversations/{id}` — Delete conversation
- `GET /api/chat/conversations/{id}/messages` — List messages
- `POST /api/chat/conversations/{id}/messages` — Send message → retrieve → generate → return reply + citations

**3. Test Chat Endpoint (Local or Production)**

First, create a conversation:
```bash
curl -X POST http://localhost:8000/api/chat/conversations \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"title": "My Numerology Question"}'
# Response: {"id": 1, "user_id": 5, "title": "My Numerology Question", "created_at": "2026-05-26T10:00:00Z"}
```

Then send a chat message:
```bash
curl -X POST http://localhost:8000/api/chat/conversations/1/messages \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"content": "Tôi sinh ngày 1/1/2000, tên là Nguyễn Văn A. Con số chủ đạo của tôi là gì?"}'
# Response 201:
# {
#   "id": 1,
#   "role": "assistant",
#   "content": "Dựa trên ngày sinh của bạn, con số chủ đạo là...",
#   "citations": [
#     {"chunk_id": 42, "document_id": 5, "text": "Excerpt from main_number..."}
#   ],
#   "created_at": "2026-05-26T10:05:30Z"
# }
```

**Note:** If KB is empty or retrieval fails, assistant responds: "Tôi không có đủ thông tin để trả lời câu hỏi này."

**4. Monitor Chat Performance**

Key logs:
- `app/routers/chat/messages.py` — retrieval latency, LLM generation time, citation extraction
- `app/services/chat/llm_service.py` — timeout events, safety-filtered responses
- `app/services/chat/retrieval_service.py` — empty result sets, similarity threshold misses

### Phase 03: User PDF Context

**Overview:** Conversations can now attach user-uploaded PDFs for hybrid KB + PDF retrieval (PDF-favored split when attached).

**1. Upload Endpoints & Configuration**

Three new endpoints (all under `/api/chat/conversations/{id}`):
- **POST upload-pdf** — Multipart form-data, single file, auto-attaches to conversation (201 on success)
- **PATCH pdf-context** — Attach/clear a previously-uploaded PDF by `pdf_context_id` (ownership validated), 200 on success
- **DELETE pdf-context** — Clear PDF attachment (does not delete the underlying UserPdfIndex), 204 on success

Add to `.env` or `.env.prod`:
```bash
USER_PDF_TTL_DAYS=30                      # Default 30, documents auto-expire if not re-uploaded
USER_PDF_MAX_BYTES=26214400               # 25MB upload limit (matches nginx config below)
PDF_CHUNK_TOKEN_WINDOW=500                # Chunking window (sync with KB)
PDF_CHUNK_OVERLAP_TOKENS=50               # Chunk overlap (sync with KB)
```

**2. Nginx Configuration**

Update `deploy/nginx.conf` (line ~40) to cap upload size at 26M (1M headroom above 25MB app cap):
```nginx
# Client upload size limit — must ≥ app's USER_PDF_MAX_BYTES
client_max_body_size 26M;
```

**Why:** App enforces 25MB with streaming size check; nginx caps at 26M so app owns the 413 contract (not nginx sending raw error page).

**3. Magic Bytes & Validation**

Router validates:
- **Magic bytes:** File must start with `%PDF-` (strict, rejects BOM/whitespace)
- **Size:** Streamed in 1MB chunks, aborts at 25MB+ with 413 (avoids full-body buffer)
- **Type:** MIME `application/pdf` confirmed

**4. Database Migration**

```bash
# Auto-applied on deploy (migration 0011_user_pdf_index.py):
# - CREATE TABLE user_pdf_index (id, user_id, pdf_hash, filename, page_count, expires_at, created_at, INDEX on expires_at)
# - CREATE TABLE user_pdf_chunks (id, pdf_index_id, page_number, content, embedding, HNSW cosine index)
# - ALTER TABLE chat_conversations ADD pdf_context_id FK (SET NULL on cascade)

# Verify:
docker compose -f docker-compose.prod.yml exec postgres psql -U numerology -d numerology \
  -c "SELECT tablename FROM pg_tables WHERE tablename IN ('user_pdf_index', 'user_pdf_chunks');"
# Expected: user_pdf_index, user_pdf_chunks
```

**5. PDF Cleanup Cron Job**

Scheduled nightly at **03:00 UTC** (file: `app/jobs/cleanup_user_pdfs.py`):
- Deletes `user_pdf_index` rows where `expires_at < now()` (cascade deletes chunks)
- Sweeps temp uploads from `/media/chat_uploads/` older than 1 hour

No manual action required; runs automatically in production.

**Edge case:** If cleanup fires while user re-uploads same PDF at exactly 03:00:00 (expired 1s ago), re-upload inserts new row (TTL = now() + 30d), so user's PDF survives. Stale ids in response rare.

**6. (Optional) Backfill Script**

If migrating existing user_reports.pdf_path PDFs to the new index:
```bash
# One-shot: computes SHA-256 hashes over user_reports.pdf_path (idempotent, skips missing files)
docker compose -f docker-compose.prod.yml exec api python -m scripts.backfill_pdf_hashes --dry-run
docker compose -f docker-compose.prod.yml exec api python -m scripts.backfill_pdf_hashes
```

Not required for Phase 03 deployment (user uploads are forward-only).

---

## Production Deployment Artifacts

All files in `deploy/` directory:

| File | Purpose | Manually Edit? |
|------|---------|----------------|
| `docker-compose.prod.yml` | Production stack definition (api + postgres + nginx) | Rarely; only for resource changes |
| `nginx.conf` | Nginx config (SSL, gzip, proxy_pass) | On domain changes; handle via Certbot for certs |
| `deploy.sh` | Main deploy script (pull → build → migrate → up) | No; version-controlled |
| `backup.sh` | Daily Postgres backup + 14-day rotation | No; version-controlled |
| `cutover.md` | Django → FastAPI migration runbook | No; archived reference |
| `rollback.md` | Rollback procedure (< 10min recovery) | No; archived reference |
| `.gitignore` | Exclude secrets from git | No |
| `env.prod.example` | Env template (safe to commit) | No; use as reference |
| `README.md` | Deployment guide (setup order, deploy one-liner) | No |

---

## Common Deployment Tasks

### Update Code Only (No DB Changes)

```bash
cd /opt/numerology/numerology-api/deploy
git pull origin main
docker compose -f docker-compose.prod.yml build api --no-cache
docker compose -f docker-compose.prod.yml up -d api
```

### Apply Database Migration

```bash
cd /opt/numerology/numerology-api/deploy
docker compose -f docker-compose.prod.yml exec api alembic upgrade head
# Verify
docker compose -f docker-compose.prod.yml logs api | head -20
```

### Reset Database (Full Wipe + Reseed)

**⚠️ DESTRUCTIVE — Use only in development or after backup!**

```bash
cd /opt/numerology/numerology-api/deploy

# 1. Stop containers
docker compose -f docker-compose.prod.yml down

# 2. Remove data volume
docker volume rm numerology_pg_data

# 3. Restart
docker compose -f docker-compose.prod.yml up -d

# 4. Migrate + seed
docker compose -f docker-compose.prod.yml exec api alembic upgrade head
docker compose -f docker-compose.prod.yml exec api python -m scripts.seed_all
docker compose -f docker-compose.prod.yml exec api python -m scripts.create_superuser --email admin@example.com --password Admin123!
```

### View Production Logs

```bash
cd /opt/numerology/numerology-api/deploy

# Real-time API logs
docker compose -f docker-compose.prod.yml logs -f api --tail=100

# Database logs
docker compose -f docker-compose.prod.yml logs -f postgres --tail=50

# Nginx logs
docker compose -f docker-compose.prod.yml logs -f nginx --tail=50

# All services
docker compose -f docker-compose.prod.yml logs -f
```

### Restart Services (No Data Loss)

```bash
cd /opt/numerology/numerology-api/deploy

# Restart single service
docker compose -f docker-compose.prod.yml restart api

# Restart all services
docker compose -f docker-compose.prod.yml restart

# Full down/up cycle (safer)
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml up -d
```

### Scale Gunicorn Workers

**Edit `docker-compose.prod.yml`, api service command:**
```yaml
command: alembic upgrade head && gunicorn app.main:app --workers=8 --worker-class=uvicorn.workers.UvicornWorker --bind=0.0.0.0:8000
```

Or via environment variable (add to `.env.prod`):
```
WEB_CONCURRENCY=8
```

Then restart: `docker compose -f docker-compose.prod.yml up -d`

---

## Monitoring & Health Checks

### Health Endpoint

```bash
curl https://api.nhansinhquan.vn/health
# → {"status":"ok"}
```

### Key Metrics to Monitor

**API Response Time:**
```bash
curl -w "Time: %{time_total}s\n" https://api.nhansinhquan.vn/health
```

**PDF Generation (Slowest Operation):**
- Target: <5s per request
- If >10s: check wkhtmltopdf process, increase workers

**Database Connections:**
```bash
docker compose -f docker-compose.prod.yml exec postgres psql -U numerology -c "SELECT count(*) FROM pg_stat_activity;"
```

**Disk Usage (Media Storage):**
```bash
docker compose -f docker-compose.prod.yml exec postgres du -sh /media
```

### Setup Sentry (Post-Launch)

1. Create Sentry project at sentry.io
2. Add to `.env.prod`: `SENTRY_DSN=https://...@sentry.io/...`
3. Install SDK: `pip install sentry-sdk`
4. Initialize in `app/main.py`:
   ```python
   import sentry_sdk
   sentry_sdk.init(
       dsn=settings.SENTRY_DSN,
       environment="production",
       traces_sample_rate=0.1,
   )
   ```

---

## Troubleshooting

### API Container Won't Start

```bash
# Check logs
docker compose -f docker-compose.prod.yml logs api

# Common causes:
# - Bad DATABASE_URL (test via psql)
# - Missing .env.prod
# - Port 8000 already in use

# Force rebuild
docker compose -f docker-compose.prod.yml build api --no-cache
docker compose -f docker-compose.prod.yml up -d api
```

### Database Connection Refused

```bash
# Check Postgres is running
docker compose -f docker-compose.prod.yml ps postgres

# Check password in DATABASE_URL
docker compose -f docker-compose.prod.yml exec postgres psql -U numerology -c "SELECT 1;"

# Restart Postgres
docker compose -f docker-compose.prod.yml restart postgres
```

### PDF Generation Fails

```bash
# Verify wkhtmltopdf installed in container
docker compose -f docker-compose.prod.yml exec api which wkhtmltopdf

# Test render
docker compose -f docker-compose.prod.yml exec api python -c "from app.utils.pdf import render_pdf; print(render_pdf('<h1>Test</h1>'))"

# If missing: update Dockerfile and rebuild
```

### SSL Certificate Renewal

```bash
# Manual renewal
certbot renew --force-renewal

# Check renewal status
certbot renew --dry-run

# Auto-renewal cron (should be pre-configured)
systemctl status certbot.timer
```

---

## Reference: Cutover from Django

**See:** `deploy/cutover.md` (full step-by-step procedure, ~30min downtime)

**High-level:**
1. Update frontend NextAuth config (DJANGO_AUTH_CLIENT_ID → new JWT realm)
2. Backup Django database
3. Set DNS TTL to 300s (5min)
4. Stop Django service
5. Start FastAPI service
6. Update Nginx upstream to FastAPI
7. Test critical paths (login, PDF generation, admin)
8. Notify users of re-login requirement
9. Monitor for 1 hour post-cutover
10. Increase DNS TTL back to 3600s

**Rollback:** See `deploy/rollback.md` (< 10min recovery via database snapshot + DNS revert)

---

## Security Checklist

- [ ] `.env.prod` excluded from git (.gitignore)
- [ ] SSL certificates auto-renewing (Certbot)
- [ ] HSTS header enabled in nginx.conf (post-first-successful-deploy)
- [ ] CORS_ORIGINS set to exact production domain (not wildcard)
- [ ] JWT_SECRET >32 chars, random (not hardcoded)
- [ ] Database password >20 chars, random (in DATABASE_URL)
- [ ] OAuth credentials stored only in .env.prod
- [ ] Daily backups running (cron job set up)
- [ ] Admin user password >12 chars, random
- [ ] Firewall allows only 22 (SSH), 80 (HTTP), 443 (HTTPS)
- [ ] VPS SSH key-only (no password auth)

---

## Disaster Recovery

### Database Backup & Restore

**Manual backup:**
```bash
docker compose -f docker-compose.prod.yml exec postgres pg_dump \
  -U numerology --format=plain numerology > backup-$(date +%Y%m%d-%H%M%S).sql
```

**Restore from backup:**
```bash
# Stop app
docker compose -f docker-compose.prod.yml down

# Remove data volume
docker volume rm numerology_pg_data

# Restart DB
docker compose -f docker-compose.prod.yml up -d postgres

# Wait for DB to be ready
sleep 10

# Restore
docker compose -f docker-compose.prod.yml exec -T postgres psql \
  -U numerology < backup-20260525-120000.sql

# Restart app
docker compose -f docker-compose.prod.yml up -d api
```

**Automated backups:** See `deploy/backup.sh` (daily 2 AM cron, 14-day rotation)

---

## Post-Launch Roadmap

- [ ] Integrate Sentry error tracking
- [ ] Set up Prometheus + Grafana metrics
- [ ] Implement ELK/Loki log aggregation
- [ ] Add rate limiting (API throttling)
- [ ] Cache numerology content in Redis
- [ ] Auto-deploy on git tags (CI/CD)
- [ ] Mobile app (React Native)

