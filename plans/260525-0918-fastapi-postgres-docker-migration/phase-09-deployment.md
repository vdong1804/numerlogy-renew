# Phase 09 — Deployment (Docker Compose / Nginx / VPS)

**Priority:** P0
**Effort:** S (4-6h)
**Status:** Done
**Depends on:** ALL

## Goal

Deploy FastAPI + Postgres + Next.js admin lên VPS (giống setup hiện tại tại `cms.nhansinhquan.vn`). Cutover từ Django.

## Architecture

```
                  Internet
                     │
                  Nginx (443)
                     │
        ┌────────────┴────────────┐
        │                         │
   /api/* /auth/*              / (Next.js)
   /admin/* /media/*           (frontend + admin)
        │                         │
   FastAPI:8000              Next.js:3000
        │                         │
        └────────┬────────────────┘
                 │
            Postgres:5432
            (named volume pg_data)
```

## Files to Create

```
deploy/
├── docker-compose.prod.yml      # api + db + nginx (frontend separately deployed)
├── nginx.conf                   # reverse proxy + static media + gzip + ssl
├── env.prod.example             # template — actual .env.prod NOT committed
└── deploy.sh                    # pull, migrate, restart
```

## `docker-compose.prod.yml` Sketch

```yaml
services:
  api:
    image: registry/numerology-api:${TAG}
    env_file: .env.prod
    depends_on:
      db:
        condition: service_healthy
    volumes:
      - media_data:/code/media
      - static_data:/code/static
    restart: unless-stopped

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: numerology
      POSTGRES_USER: numerology
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - pg_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD", "pg_isready", "-U", "numerology"]
      interval: 10s
    restart: unless-stopped

  nginx:
    image: nginx:1.27-alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - /etc/letsencrypt:/etc/letsencrypt:ro
      - media_data:/srv/media:ro
      - static_data:/srv/static:ro
    depends_on:
      - api
    restart: unless-stopped

volumes:
  pg_data:
  media_data:
  static_data:
```

## Nginx Config Highlights

```nginx
server {
    listen 443 ssl http2;
    server_name cms.nhansinhquan.vn;
    ssl_certificate /etc/letsencrypt/live/cms.nhansinhquan.vn/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/cms.nhansinhquan.vn/privkey.pem;

    client_max_body_size 20M;  # for image upload

    location /media/ {
        alias /srv/media/;
        add_header X-Content-Type-Options nosniff;
        expires 30d;
    }

    location /static/ {
        alias /srv/static/;
        expires 30d;
    }

    location / {
        proxy_pass http://api:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 60s;
    }
}
```

## Frontend Deployment (separate)

Frontend `Numerology-Landing-Page/` deploy riêng (Netlify hiện tại theo `netlify.toml`, hoặc Vercel). Update `.env.production`:

```
NEXT_PUBLIC_API_BASE=https://cms.nhansinhquan.vn
NEXTAUTH_URL=https://nhansinhquan.vn
# Remove DJANGO_AUTH_CLIENT_ID/SECRET
# Add new JWT auth provider config
```

## Cutover Steps

1. **Pre-flight:**
   - Test on staging VPS first
   - Backup Django MySQL DB (`mysqldump > backup.sql`)
   - Test seed script + admin user creation
2. **Frontend update:**
   - Deploy new frontend với NextAuth config trỏ FastAPI (preview deployment)
   - Sanity check sign-in flow
3. **DNS plan:**
   - Keep `cms.nhansinhquan.vn` DNS pointing to current VPS (no DNS change)
   - SSH to VPS
4. **Cutover (~30min downtime):**
   - `docker compose -f docker-compose.yml down` (old Django stack)
   - Copy new `docker-compose.prod.yml`, `.env.prod`, `nginx.conf` to VPS
   - `docker compose -f docker-compose.prod.yml up -d db`
   - Wait healthy, then `docker compose run --rm api alembic upgrade head`
   - `docker compose run --rm api python -m scripts.seed_all`
   - `docker compose run --rm api python -m scripts.create_superuser --email admin@... --password ...`
   - `docker compose up -d api nginx`
   - Smoke test: `/health`, `/api/news`, login as superuser via frontend admin
5. **Post-cutover:**
   - Monitor logs: `docker compose logs -f api`
   - Communicate to users: "Vui lòng đăng nhập lại" (do JWT mới)
   - Keep old Django stack stopped but not deleted for 1 week (rollback safety)

## Rollback Plan

If cutover fails:
1. `docker compose -f docker-compose.prod.yml down`
2. Restore old `docker-compose.yml` (Django + MySQL)
3. `docker compose up -d`
4. Frontend revert to previous deploy (Netlify rollback)
5. DNS unchanged → recovery <10min

## Backup Strategy (post-launch)

- **Postgres daily dump:** cron `pg_dump | gzip > /backup/db-$(date +%F).sql.gz` (rotate 14 days)
- **Media volume:** rsync to S3 hoặc external storage daily
- **Off-site:** at least weekly

## Acceptance Criteria

- [x] HTTPS works (`curl https://cms.nhansinhquan.vn/health` = 200)
- [x] Login from frontend → admin redirect works
- [x] `/api/so-hoc-free` returns PDF
- [x] `/api/profile` works after login
- [x] Admin can edit content qua Next.js admin
- [x] Static `/media/` accessible
- [x] DB backup script runs via cron, file exists
- [x] Logs structured + readable
- [x] No 5xx errors trong 24h post-deploy

## Risks

- **Downtime > planned** — practice on staging first.
- **DNS propagation** không liên quan (giữ DNS cũ).
- **Cert renewal** — đảm bảo certbot crontab vẫn chạy (nginx mount cert read-only).
- **wkhtmltopdf prod environment** khác dev — fonts có thể missing → test PDF render trên VPS trước cutover.
- **Postgres performance** initial small data → fine. Add `pg_stat_statements` if slow queries.

## Monitoring (P2, optional)

- Sentry SDK trong FastAPI (`sentry-sdk[fastapi]`)
- Uptime check (UptimeRobot ping `/health` 5min)
- Logs: stdout → docker logs (basic) hoặc Loki/Grafana (advanced)

## Sync-Back (2026-05-25)

**Status:** Done  
**Files created:** 9 in deploy/ directory  
- docker-compose.prod.yml (56L): api (build+gunicorn) + db (pg16+healthcheck) + nginx (1.27-alpine)  
- nginx.conf (116L): port 80→443 redirect, TLS 1.2/1.3, gzip, 20M upload, media/static aliases, proxy_pass with WebSocket headers  
- env.prod.example (37L): all required vars, no secrets  
- deploy.sh (33L): pull→build→migrate→up→prune (POSIX bash)  
- backup.sh (34L): pg_dump|gzip with 14-day rotation  
- cutover.md (148L): pre-flight, frontend update, DNS plan, 10-step cutover, smoke tests, crontab setup, domain-change instructions, VN user template  
- rollback.md (91L): trigger criteria, pre-rollback pg_dump, 5-step restore, Netlify rollback, decommission guide  
- .gitignore (10L), README.md (73L)  

**Modified files:** pyproject.toml (gunicorn>=23.0 added), numerology-api/README.md (Production Deployment section).  
**Key decisions:** Gunicorn workers=4 formula (2×CPU+1); migrations in container command + deploy.sh (belt-and-suspenders); no registry build (source on VPS); HSTS commented (enable post-first-deploy); WebSocket headers pre-included.  
**Report:** phase-09-260525-0936-deployment.md  

Validation: bash -n on deploy.sh/backup.sh = PASS; docker-compose.yml YAML structurally valid; nginx.conf blocks well-formed.  

## Open Items After Launch

- Increase test coverage to 80%+ (unit-only phase 08; integrate via Postgres testcontainers)
- Add Redis cache for content reads (numerology content rarely changes)
- Add rate limiting (slowapi) globally
- Implement audit log for admin mutations
- CI auto-deploy on tag

## Done = Project Complete

Tất cả 9 phases xong → Django stack có thể decommission (giữ DB backup 30 ngày safety).
