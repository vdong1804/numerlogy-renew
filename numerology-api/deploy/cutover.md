# Cutover Runbook — Django → FastAPI (cms.nhansinhquan.vn)

Estimated downtime: **~30 minutes**. Practice on staging VPS first.

---

## Pre-flight Checklist

- [ ] Staging deploy confirmed working end-to-end
- [ ] PDF render tested on VPS (wkhtmltopdf + Vietnamese fonts)
- [ ] `mysqldump` backup of Django DB taken and verified
  ```bash
  mysqldump -u root -p django_db > /backup/django-$(date +%F).sql
  ```
- [ ] `.env.prod` filled from `env.prod.example` (secrets from password manager)
- [ ] Let's Encrypt cert already issued for `cms.nhansinhquan.vn`
  ```bash
  certbot certonly --webroot -w /var/www/certbot -d cms.nhansinhquan.vn
  ```
- [ ] `deploy/` files copied to VPS at `/opt/numerology-api/deploy/`
- [ ] Seed scripts tested on staging (idempotent)
- [ ] Frontend preview deployment smoke-tested (NextAuth → FastAPI)
- [ ] Backup cron installed (see section below)

---

## Frontend Deployment Update

Update `Numerology-Landing-Page/.env.production` before cutover:

```env
NEXT_PUBLIC_API_BASE=https://cms.nhansinhquan.vn
NEXTAUTH_URL=https://nhansinhquan.vn
# Remove any DJANGO_AUTH_CLIENT_ID / DJANGO_AUTH_CLIENT_SECRET entries
```

Deploy preview to Netlify, confirm sign-in flow works against staging API.
Keep old Netlify deploy as fallback (do not delete — use "Publish deploy" to revert).

---

## DNS Plan

**No DNS change required.** `cms.nhansinhquan.vn` stays pointed at the same VPS IP.
Only the process listening on port 80/443 changes (old Django/Nginx → new Docker Nginx).

---

## Cutover Steps

SSH into VPS as deploy user. All commands run from `/opt/numerology-api/deploy/`.

### 1 — Stop old Django stack
```bash
cd /opt/django-numerology   # or wherever old stack lives
docker compose down          # or: systemctl stop gunicorn nginx
```

### 2 — Pull latest FastAPI code
```bash
cd /opt/numerology-api
git pull --rebase
```

### 3 — Ensure `.env.prod` is in place
```bash
ls -la /opt/numerology-api/deploy/.env.prod   # must exist
```

### 4 — Start Postgres
```bash
cd /opt/numerology-api/deploy
docker compose -f docker-compose.prod.yml up -d db
# Wait for healthy
docker compose -f docker-compose.prod.yml ps db
```

### 5 — Run migrations
```bash
docker compose -f docker-compose.prod.yml run --rm api alembic upgrade head
```

### 6 — Seed database
```bash
# Content, packages, banks
docker compose -f docker-compose.prod.yml run --rm api python -m scripts.seed_all

# Create superuser (interactive — choose strong password)
docker compose -f docker-compose.prod.yml run --rm api python -m scripts.create_superuser \
  --email admin@nhansinhquan.vn \
  --password "$(openssl rand -base64 24)" \
  --first-name Admin \
  --last-name User
```
Note the generated password before the terminal closes!

### 7 — Start API + Nginx
```bash
docker compose -f docker-compose.prod.yml up -d api nginx
```

### 8 — Smoke tests (see section below)

### 9 — Publish frontend to production
In Netlify dashboard: promote the preview deploy created in pre-flight to production.

### 10 — Notify users (see template below)

---

## Smoke Test Commands

Run from your local machine or VPS:

```bash
BASE=https://cms.nhansinhquan.vn

# Health check
curl -f "$BASE/health"
# Expected: {"status":"ok"}

# OpenAPI docs accessible
curl -o /dev/null -sw "%{http_code}" "$BASE/docs"
# Expected: 200

# Public news list
curl -f "$BASE/api/news?limit=3"

# Free numerology endpoint (unauthenticated)
curl -o /dev/null -sw "%{http_code}" "$BASE/api/so-hoc-free"
# Expected: 422 (missing body) — proves endpoint is reachable

# Static media reachable (replace with a known media path after seeding)
# curl -o /dev/null -sw "%{http_code}" "$BASE/media/some-image.jpg"
```

Check logs for errors:
```bash
docker compose -f docker-compose.prod.yml logs --tail=100 api
docker compose -f docker-compose.prod.yml logs --tail=50 nginx
```

---

## Backup Cron Setup

Install cron job as root (edit with `crontab -e`):
```cron
# Daily Postgres backup at 02:00
0 2 * * * /opt/numerology-api/deploy/backup.sh >> /var/log/numerology-backup.log 2>&1
```

Ensure script is executable:
```bash
chmod +x /opt/numerology-api/deploy/backup.sh
```

---

## Post-Cutover Monitoring

- **Logs:** `docker compose -f docker-compose.prod.yml logs -f api`
- **Uptime:** Configure UptimeRobot to ping `https://cms.nhansinhquan.vn/health` every 5 min
- **Cert renewal:** certbot cron must still run (cert is bind-mounted read-only into nginx)
  ```bash
  certbot renew --dry-run   # verify renewal works
  ```
- **DB size:** `docker compose exec db psql -U numerology -c '\l+'`
- Monitor for 5xx errors in nginx access log for first 24h

---

## Cert Renewal (post-deploy)

Nginx mounts `/etc/letsencrypt` read-only. After certbot renews, reload nginx:
```bash
docker compose -f docker-compose.prod.yml exec nginx nginx -s reload
```
Add to certbot renewal hook (`/etc/letsencrypt/renewal-hooks/deploy/`):
```bash
#!/bin/bash
docker compose -f /opt/numerology-api/deploy/docker-compose.prod.yml exec nginx nginx -s reload
```

---

## To Change the Domain

1. Update `server_name` in `nginx.conf`
2. Update cert path references in `nginx.conf` (2 occurrences)
3. Update `ALLOWED_ORIGINS`, `OAUTH_REDIRECT_BASE` in `.env.prod`
4. Reissue cert: `certbot certonly --webroot -w /var/www/certbot -d new.domain.vn`
5. `docker compose -f docker-compose.prod.yml up -d --force-recreate nginx`

---

## User Communication Template

Post in app / send email after cutover:

> **[Tiếng Việt]**
> Hệ thống vừa được nâng cấp lên phiên bản mới. Vui lòng **đăng nhập lại** để tiếp tục sử dụng dịch vụ.
> Nếu gặp sự cố, vui lòng liên hệ hỗ trợ qua email: support@nhansinhquan.vn
>
> **[English]**
> The system has been upgraded. Please **log in again** to continue. Your data is safe.
> Contact support@nhansinhquan.vn if you experience any issues.
