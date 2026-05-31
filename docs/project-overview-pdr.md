# Project Overview & PDR

**Project:** Numerology API Platform  
**Version:** 1.0 (Post-Migration)  
**Last Updated:** 2026-05-25

---

## Product Overview

Numerology platform provides personalized numerology readings and horoscope charts via REST API, with content management admin interface. Users register, authenticate via JWT or OAuth (Google/Facebook), and access:

- **Free readings** (phone number validation only)
- **Paid PDF downloads** (quota-based, charges per package)
- **Content library** (22 numerology content tables + news + horoscopes)

Backend migrated from Django 4.2 + MySQL to **FastAPI + PostgreSQL 16 + Docker** (2026-05-25).

---

## Target Users

| User Type | Tools | Needs |
|-----------|-------|-------|
| **End User** | Mobile/Web | Quick numerology calc, PDF downloads, email/password account |
| **Content Manager** | Next.js Admin | Edit numerology content, manage news/packages/payments via web UI |
| **Developer** | API Docs + CLI | FastAPI async/await patterns, ORM schema, deployment playbooks |
| **DevOps** | Docker/Nginx | Production deploy, backups, rollback procedures |

---

## Current Architecture

```
Frontend (Next.js)
├── Public Pages: landing, numerology calc
├── Admin: /admin/* (login → content/news/packages/users/payments CRUD)
└── Auth: JWT localStorage + Bearer token

Backend (FastAPI)
├── Core: numerology calc, OAuth, JWT
├── APIs: auth, profile, numerology (free/paid), content, news, packages, payments
├── DB: PostgreSQL 16 (31 tables: 22 numerology, 4 user, 5 business)
└── File Storage: media (PDFs, images) + uploads folder

Infra (Docker)
├── api: FastAPI + Gunicorn (4 workers)
├── db: PostgreSQL 16 + persistent volume
└── nginx: SSL termination, gzip, reverse proxy
```

---

## Feature List

### Authentication (Phase 03 — Done)
- Email/password register & login → JWT access + refresh token
- Refresh token rotation (15min access, 7day refresh)
- Forgot / reset password via email link (hashed single-use token, 30min expiry, revokes refresh tokens on use)
- Superuser role for admin access
- SNS login (Google/Facebook/Twitter) removed 2026-05-25; users authenticate exclusively with email + password

### Numerology Calculations (Phase 04 — Done)
- Free reading: phone + name → calculated numbers (9 types)
- Paid reading: JWT auth → quota check → decrement quota → PDF (via wkhtmltopdf)
- Horoscope chart: vietheart.net async fetch
- Edge cases: master numbers (11/22/33), zero wraps, accented text

### Content & Utilities (Phase 05 — Done)
- 22 numerology content tables (attitude, balance, challenge, etc.) + seeding
- News CRUD (title, slug, html_content, featured_image)
- Package management: PDF downloads (quota-based) + Chat AI add-ons (message packs, 30d validity)
- Bank info (name, code, account, icon_url)
- User profiles (birthday, gender, address, quota)

### Admin UI (Phase 06 — Done)
- Content editor: TipTap rich-text, image upload, table support
- CRUD: news, packages, banks, numerology content (all 23 tables)
- User management: view, edit, delete
- Payment approval: approve/reject with reason + history
- Vietnamese labels throughout

### Payments (Phase 05 — Done)
- User payments table: amount, status (pending/approved/rejected), bank, reference
- Package purchase: auto-create user_packages + log in user_payments
- Admin approval: confirm received payment → update quota

### Chatbot Hardening & Launch Readiness (Phase 08 — Done)
- Cost monitoring + alerts, abuse detection (5 patterns), CAPTCHA gate, feature flag with rollout %, A/B variants, DSAR endpoint
- See ops guides: [`chatbot-runbook.md`](./chatbot-runbook.md), [`chatbot-launch-checklist.md`](./chatbot-launch-checklist.md), [`chatbot-cost-monitoring.md`](./chatbot-cost-monitoring.md)

### Seeding & Fixtures (Phase 07 — Done)
- 22 content tables + 3 packages + 1 bank + sample superuser
- Idempotent scripts: `seed_content.py`, `seed_packages.py`, `seed_banks.py`
- Production: replace via admin UI before go-live

### Deployment (Phase 09 — Done)
- Docker Compose: api + db + nginx on single VPS
- Nginx: SSL (Certbot), gzip, media/static serving
- Alembic: zero-downtime migrations via `upgrade head`
- Backup: daily pg_dump, 14-day rotation
- Cutover & rollback runbooks

---

## Migration Context (Django → FastAPI)

| Aspect | Was (Django) | Now (FastAPI) | Impact |
|--------|--------------|---------------|--------|
| Framework | Django 4.2 + DRF | FastAPI 0.115+ | Async by default, auto OpenAPI docs |
| DB | MySQL 8.0 | PostgreSQL 16 | JSONB, full-text search, async drivers |
| Auth | django-oauth-toolkit + drf-social-oauth2 | python-jose JWT + email-link reset | SNS removed; users re-login with email/password |
| Admin | Django admin + CKEditor | Next.js custom UI + TipTap | Standalone, decoupled from API |
| PDF | Django templates + pdfkit | Jinja2 + wkhtmltopdf | Simpler templates, async render |
| Tests | Django test framework | Pytest + asyncio | Better coverage, faster loops |
| Deploy | Gunicorn + systemd (old) | Gunicorn + Docker Compose | Reproducible, cloud-ready |

**Users must re-authenticate after go-live** (new JWT realm).

---

## Development Roadmap (Post-Launch)

### Next 30 Days
- Integration tests via testcontainers (PostgreSQL)
- Coverage increase to 80% (currently ~70%)
- Redis cache for content reads (numerology tables)
- Sentry error tracking integration

### Q3+ (Future)
- Mobile app (React Native)
- Real-time features (WebSocket notifications for payment approval)
- Multi-tenancy (per plan: out-of-scope now)
- Admin audit log for all mutations

---

## Success Criteria

- ✅ All 9 phases completed (features shipped, 70%+ test coverage)
- ✅ Production deployed on VPS
- ✅ Cutover < 1hr downtime
- ✅ Zero data loss
- ✅ Admin UI operational (content edits live in <30s)
- ✅ PDF generation <5s per request
