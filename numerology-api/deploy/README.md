# Deploy — Production Artifacts

Files in this directory drive the production deployment of `numerology-api` on the VPS at `cms.nhansinhquan.vn`.

## File Map

| File | Purpose |
|------|---------|
| `docker-compose.prod.yml` | Production stack: api + db + nginx (no dev ports exposed) |
| `nginx.conf` | Reverse proxy, SSL termination, static/media serving, gzip |
| `env.prod.example` | Template for `.env.prod` — copy and fill secrets |
| `deploy.sh` | Pull → build → migrate → restart (run on VPS for each deploy) |
| `backup.sh` | Daily Postgres dump with 14-day rotation (run via cron) |
| `cutover.md` | Step-by-step cutover runbook (Django → FastAPI, ~30min downtime) |
| `rollback.md` | Rollback runbook if cutover fails (recovery < 10min) |
| `.gitignore` | Keeps `.env.prod`, logs, certbot-webroot/ out of git |

## First-Time Setup Order

**1. Copy and fill env file**
```bash
cp deploy/env.prod.example deploy/.env.prod
# Edit .env.prod — fill POSTGRES_PASSWORD, JWT_SECRET, OAuth creds, origins
```

Generate JWT secret:
```bash
python -c "import secrets; print(secrets.token_hex(64))"
```

**2. Obtain TLS certificate** (before starting nginx)
```bash
# Temporarily start nginx on port 80 only (edit nginx.conf to remove 443 block),
# or use certbot standalone mode:
certbot certonly --standalone -d cms.nhansinhquan.vn
# Then restore nginx.conf and proceed
```

**3. Run first deploy**
```bash
# On VPS, from repo root:
chmod +x deploy/deploy.sh deploy/backup.sh
bash deploy/deploy.sh
```

The script: pulls code → builds API image → starts db → runs Alembic migrations → starts all services.

**4. Seed the database** (first deploy only)
```bash
cd deploy
docker compose -f docker-compose.prod.yml run --rm api python -m scripts.seed_all
docker compose -f docker-compose.prod.yml run --rm api python -m scripts.create_superuser \
  --email admin@nhansinhquan.vn --password "STRONG_PASSWORD"
```

**5. Install backup cron**
```bash
# Add to crontab (crontab -e):
0 2 * * * /opt/numerology-api/deploy/backup.sh >> /var/log/numerology-backup.log 2>&1
```

## Subsequent Deploys

```bash
bash /opt/numerology-api/deploy/deploy.sh
```

## Big Events

- **Planned cutover from Django:** follow `cutover.md`
- **Rollback needed:** follow `rollback.md`

## Domain Change

Search-replace `cms.nhansinhquan.vn` in `nginx.conf` (2 occurrences in cert paths, 1 in server_name),
update `ALLOWED_ORIGINS` / `OAUTH_REDIRECT_BASE` in `.env.prod`, re-issue cert, reload nginx.

## Frontend

`Numerology-Landing-Page/` deploys separately via Netlify (`netlify.toml`).
See `cutover.md` → "Frontend Deployment Update" for env vars to set.
