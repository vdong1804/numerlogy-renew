# Rollback Runbook — FastAPI → Django

Use this if the FastAPI cutover fails and the old Django stack must be restored.

Expected recovery time: **< 10 minutes** (DNS unchanged, old stack stopped not deleted).

---

## When to Rollback

Trigger rollback if ANY of the following within first hour post-cutover:

- `/health` returns non-200 for > 2 minutes
- Login flow broken (OAuth or JWT failures) and not fixable in < 5 min
- PDF generation returning 500 errors
- Database migration failed or data corruption suspected
- Nginx SSL errors preventing any HTTPS access
- Error rate > 5% in logs sustained > 5 minutes

**Do not rollback for:** single slow request, one user report, minor UI bug fixable in code.

---

## Pre-Rollback: Backup New Postgres Data

If any real user data was written during the FastAPI window, dump it before destroying:

```bash
cd /opt/numerology-api/deploy

# Dump new Postgres data (in case partial data needs recovery later)
docker compose -f docker-compose.prod.yml exec -T db \
    pg_dump -U numerology numerology \
    | gzip > /backup/fastapi-rollback-$(date +%F-%H%M).sql.gz

echo "Backup written, size: $(ls -lh /backup/fastapi-rollback-*.sql.gz | tail -1)"
```

---

## Rollback Steps

### 1 — Stop FastAPI stack (keep volumes, don't prune)
```bash
cd /opt/numerology-api/deploy
docker compose -f docker-compose.prod.yml down
# Do NOT run: docker compose down -v  (that destroys pg_data volume)
```

### 2 — Restore old Django stack
```bash
cd /opt/django-numerology   # adjust path to old Django project
docker compose up -d         # or: systemctl start gunicorn nginx
```

### 3 — Verify Django is up
```bash
curl -f http://localhost:8000/health   # or whatever Django health URL
# Check nginx is serving HTTPS again
curl -o /dev/null -sw "%{http_code}" https://cms.nhansinhquan.vn/
```

### 4 — Frontend rollback
In Netlify dashboard:
1. Go to Deploys tab for `nhansinhquan.vn`
2. Find the previous production deploy (before the FastAPI-targeted one)
3. Click "Publish deploy" → confirm

This reverts `NEXT_PUBLIC_API_BASE` and NextAuth config back to Django endpoints.

### 5 — Verify frontend login works
Sign in via the frontend. Confirm session established with Django backend.

---

## DNS

No DNS changes are needed. `cms.nhansinhquan.vn` stays pointed at the same VPS.
Recovery is purely a process swap on the VPS.

---

## Post-Rollback

- Document what failed (issue + logs) before attempting cutover again
- Keep FastAPI volumes (`pg_data`, `media_data`, `static_data`) intact for investigation
  — only remove after root cause is confirmed fixed on staging
- Keep old Django stack running for minimum 1 week after successful re-cutover
- File GitHub issue or internal ticket with failure details

---

## Decommission Old Django Stack (after confirmed stable)

Only after FastAPI has been stable for >= 7 days:

```bash
# Final Django DB backup before decommission
mysqldump -u root -p django_db | gzip > /backup/django-final-$(date +%F).sql.gz

# Stop and remove old stack
cd /opt/django-numerology
docker compose down -v   # or remove manually

# Keep backup for 30 days minimum
```
