# Deployment — nhansinhquan.vn

One Docker stack runs **both** apps + Postgres. TLS termination and reverse
proxy are handled by **your own nginx on the host** (not part of this stack).

| Subdomain | Service | Upstream | Source |
|-----------|---------|----------|--------|
| `nhansinhquan.vn`, `www.nhansinhquan.vn` | Next.js landing page | `127.0.0.1:3003` | `../Numerology-Landing-Page` |
| `api.nhansinhquan.vn` | FastAPI backend (+ `/media`, `/static`) | `127.0.0.1:8000` | `../numerology-api` |
| `cms.nhansinhquan.vn` | FastAPI admin / CMS | `127.0.0.1:8000` | `../numerology-api` |

Stack: `frontend` + `api` + `db` (Postgres 16 + pgvector). No `nginx`/`certbot`.

## Files

| File | Purpose |
|------|---------|
| `docker-compose.prod.yml` | The app stack — publishes `127.0.0.1:3003` (frontend) and `127.0.0.1:8000` (api) |
| `.env.prod.example` | Env template → copy to `.env.prod`, fill secrets |
| `deploy.sh` | Pull → build → migrate → restart (run every deploy) |
| `backup.sh` | Daily Postgres dump, 14-day rotation (cron) |

## Prerequisites

- A Linux server with Docker + Docker Compose v2.
- DNS **A records** for all four subdomains → server IP.
- **nginx installed on the host** with TLS (you configure this yourself).

## First-time setup

```bash
cd deploy

# 1. Fill secrets
cp .env.prod.example .env.prod
nano .env.prod          # POSTGRES_PASSWORD, JWT_SECRET, DEEPSEEK_API_KEY, GEMINI_API_KEY, etc.
# Generate JWT secret:  python3 -c "import secrets; print(secrets.token_hex(64))"

# 2. Build + migrate + start the app stack
bash deploy.sh

# 3. Seed the database (first deploy only)
docker compose -f docker-compose.prod.yml --env-file .env.prod run --rm api python -m scripts.seed_all
docker compose -f docker-compose.prod.yml --env-file .env.prod run --rm api \
  python -m scripts.create_superuser --email admin@nhansinhquan.vn --password "STRONG_PASSWORD"

# 3b. Seed media files into the runtime volume (blog images + sample reports the
#     seeded DB rows point at). They live in the repo but the image excludes
#     ./media (it is a volume), so copy them in once. sudo because the container
#     created ./media as root.
sudo cp -rn ../numerology-api/media/. ./media/ && sudo chmod -R a+rX ./media

# 4. Configure your host nginx + TLS, then verify:
curl http://127.0.0.1:8000/health     # → {"status":"ok"}
```

## Subsequent deploys

```bash
cd deploy && bash deploy.sh
```

Pulls latest code, rebuilds frontend + api images, runs Alembic migrations, restarts.

> **Note:** `NEXT_PUBLIC_*` values are baked into the frontend bundle at build
> time. Changing them in `.env.prod` only takes effect after `deploy.sh` rebuilds
> the frontend image (it always does).

## Host nginx (you configure this)

The containers only listen on `127.0.0.1`. Configure your own nginx + TLS on
the host to terminate TLS and reverse-proxy to them:

- Frontend → `http://127.0.0.1:3003`
- API + CMS → `http://127.0.0.1:8000`
- Serve `/media` and `/static` directly from the `./media` and `./static` bind-mounts.

## Backups (cron)

```bash
crontab -e
# Daily 02:00 dump with 14-day retention:
0 2 * * * /full/path/to/deploy/backup.sh >> /var/log/numerology-backup.log 2>&1
```

## Common operations

```bash
C="docker compose -f docker-compose.prod.yml --env-file .env.prod"

$C logs -f                 # all logs
$C logs -f api             # backend only
$C ps                      # service status
$C down                    # stop stack (keeps volumes/data)
```

## Notes

- `db` uses `pgvector/pgvector:pg16` because Alembic migration `0010` (chatbot
  RAG KB tables) requires the `vector` extension.
- `TRUSTED_PROXY_MODE`: keep `direct` if the host nginx connects over plain
  `127.0.0.1` and forwards `X-Forwarded-Proto`. Switch to `cloudflare` only if
  Cloudflare proxy sits in front.
