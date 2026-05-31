# Phase 09 — Deployment Report

**Status:** Completed
**Date:** 2026-05-25

---

## Files Created

```
numerology-api/deploy/
├── docker-compose.prod.yml   (56 lines)
├── nginx.conf                (116 lines)
├── env.prod.example          (37 lines)
├── deploy.sh                 (33 lines)
├── backup.sh                 (34 lines)
├── cutover.md                (148 lines)
├── rollback.md               (91 lines)
├── .gitignore                (10 lines)
└── README.md                 (73 lines)
```

**Modified:**
- `numerology-api/pyproject.toml` — added `gunicorn>=23.0` to dependencies
- `numerology-api/README.md` — added "Production Deployment" section linking deploy/README.md

---

## Tasks Completed

- [x] Created `deploy/` directory
- [x] `docker-compose.prod.yml` — api (build+gunicorn cmd) + db (pg16, healthcheck) + nginx (1.27-alpine); no external ports on api/db; named volumes pg_data/media_data/static_data; certbot-webroot volume for ACME
- [x] `nginx.conf` — port 80→443 redirect (ACME pass-through), TLS 1.2/1.3, modern ciphers, gzip, 20M upload, media/static aliases with cache headers, proxy_pass with all forwarding headers + WebSocket upgrade
- [x] `env.prod.example` — all required vars, no real secrets
- [x] `deploy.sh` — pull→build→db-wait→migrate→up→prune; POSIX bash
- [x] `backup.sh` — pg_dump|gzip, 14-day rotation, size sanity check; crontab line in cutover.md
- [x] `cutover.md` — pre-flight checklist, frontend update, DNS plan, 10-step numbered cutover, smoke tests, backup cron setup, cert renewal hook, domain-change instructions, VN user notification template
- [x] `rollback.md` — trigger criteria, pre-rollback pg dump, 5-step restore, frontend Netlify rollback, decommission guide
- [x] `.gitignore` — excludes .env.prod, certbot-webroot/, *.log
- [x] `deploy/README.md` — file map table, first-time setup order, subsequent deploy one-liner
- [x] `pyproject.toml` — gunicorn>=23.0 added
- [x] `numerology-api/README.md` — Production Deployment section added

---

## Validation

| Check | Result |
|-------|--------|
| `bash -n deploy.sh` | PASS |
| `bash -n backup.sh` | PASS |
| `python yaml.safe_load(docker-compose.prod.yml)` | PASS |
| `docker compose config` | SKIP — .env.prod intentionally absent on dev machine; YAML structurally valid |
| nginx.conf | Visual inspect — blocks well-formed, no unclosed braces |

---

## Key Decisions

- **Gunicorn workers = 4** — conservative for typical 2-4 vCPU VPS; (2×CPU+1) formula → adjust via `WEB_CONCURRENCY` env var if needed
- **Migrations in `command:`** — runs `alembic upgrade head` before gunicorn starts; safer than deploy.sh-only because a fresh container restart also migrates; deploy.sh also runs it explicitly as belt-and-suspenders
- **No build registry** — builds from source on VPS (simpler for solo/small team); swap `build:` for `image: registry/...` when CI/CD added
- **HSTS commented out** — enable after first successful HTTPS deploy to avoid locking out on config errors
- **WebSocket headers included** — future-proofs for any WS endpoints without needing nginx.conf edit

---

## Open Items

- Nginx `http2` directive deprecated in nginx ≥ 1.25 (use `listen 443 ssl; http2 on;` syntax). nginx 1.27-alpine supports both; current config works but may log deprecation warning — update when next touching nginx.conf.
- `static_data` volume populated only if app calls `collectstatic` — FastAPI/uvicorn doesn't have Django's collectstatic; volume exists for future use (e.g. admin JS served from /static/). Currently empty; `/static/` location harmless.
- Sentry SDK integration noted in plan as P2 (not implemented — YAGNI until post-launch).
- CI auto-deploy on git tag noted as post-launch item.
