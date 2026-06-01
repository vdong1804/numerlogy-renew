# Unified Deployment — nhansinhquan.vn

One Docker stack deploys **both** projects behind a single nginx + Let's Encrypt TLS.

| Subdomain | Service | Source |
|-----------|---------|--------|
| `nhansinhquan.vn`, `www.nhansinhquan.vn` | Next.js landing page | `../Numerology-Landing-Page` |
| `api.nhansinhquan.vn` | FastAPI backend (+ `/media`, `/static`) | `../numerology-api` |
| `cms.nhansinhquan.vn` | FastAPI admin / CMS | `../numerology-api` |

Stack: `frontend` + `api` + `db` (Postgres 16 + pgvector) + `nginx` + `certbot`.

## Files

| File | Purpose |
|------|---------|
| `docker-compose.prod.yml` | The full stack (no host ports except nginx 80/443) |
| `nginx.conf` | Reverse proxy, TLS, per-subdomain routing, media/static, SSE |
| `.env.prod.example` | Env template → copy to `.env.prod`, fill secrets |
| `deploy.sh` | Pull → build → migrate → restart (run every deploy) |
| `init-letsencrypt.sh` | One-time TLS cert issuance for all 4 subdomains |
| `backup.sh` | Daily Postgres dump, 14-day rotation (cron) |

## Prerequisites

- A Linux server with Docker + Docker Compose v2.
- DNS **A records** for all four subdomains → server IP:
  `nhansinhquan.vn`, `www`, `api`, `cms`.
- Ports **80** and **443** open.

## First-time setup

```bash
cd deploy

# 1. Fill secrets
cp .env.prod.example .env.prod
nano .env.prod          # POSTGRES_PASSWORD, JWT_SECRET, DEEPSEEK_API_KEY, GEMINI_API_KEY, etc.

# Generate JWT secret:
#   python3 -c "import secrets; print(secrets.token_hex(64))"

# 2. Obtain TLS certificates (once). Test first with STAGING=1 to dodge rate limits:
STAGING=1 bash init-letsencrypt.sh you@email.com   # dry run
bash init-letsencrypt.sh you@email.com             # real cert

# 3. Build + migrate + start everything
bash deploy.sh

# 4. Seed the database (first deploy only)
docker compose -f docker-compose.prod.yml --env-file .env.prod run --rm api python -m scripts.seed_all
docker compose -f docker-compose.prod.yml --env-file .env.prod run --rm api \
  python -m scripts.create_superuser --email admin@nhansinhquan.vn --password "STRONG_PASSWORD"
```

Verify:

```bash
curl https://api.nhansinhquan.vn/health        # → {"status":"ok"}
# open https://nhansinhquan.vn in a browser
```

## Subsequent deploys

```bash
cd deploy && bash deploy.sh
```

Pulls latest code, rebuilds frontend + api images, runs Alembic migrations, restarts.

> **Note:** `NEXT_PUBLIC_*` values are baked into the frontend bundle at build
> time. Changing them in `.env.prod` only takes effect after `deploy.sh`
> rebuilds the frontend image (it always does).

## Backups (cron)

```bash
crontab -e
# Daily 02:00 dump with 14-day retention:
0 2 * * * /full/path/to/Numerlogy/deploy/backup.sh >> /var/log/numerology-backup.log 2>&1
```

## TLS renewal

The `certbot` service auto-renews every 12h; nginx reloads every 6h to pick up
new certs. No manual action needed.

## Common operations

```bash
C="docker compose -f docker-compose.prod.yml --env-file .env.prod"

$C logs -f                 # all logs
$C logs -f api             # backend only
$C ps                      # service status
$C restart nginx           # reload after editing nginx.conf
$C down                    # stop stack (keeps volumes/data)
```

## Notes

- The old single-project setup at `../numerology-api/deploy/` (CMS-only,
  `cms.nhansinhquan.vn`) is superseded by this unified stack. Use this one.
- `db` uses `pgvector/pgvector:pg16` because Alembic migration `0010` (chatbot
  RAG KB tables) requires the `vector` extension.
- `TRUSTED_PROXY_MODE=direct` because this nginx is the public edge. Switch to
  `cloudflare` only if you put Cloudflare proxy in front.
