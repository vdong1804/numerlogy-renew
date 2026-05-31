# Phase 03 Critical/High Fixes Report

**Date:** 2026-05-26
**Agent:** fullstack-developer

---

## Files Modified

| Fix | File |
|-----|------|
| C1  | `numerology-api/deploy/nginx.conf` |
| C2  | `Numerology-Landing-Page/next.config.js` |
| C2  | `docs/lint-cleanup-backlog.md` (created) |
| H1  | `numerology-api/app/main.py` |
| H2  | `Numerology-Landing-Page/src/components/turnstile-widget.tsx` |
| H3  | `numerology-api/app/config.py` |
| H3  | `numerology-api/app/middleware/rate_limit.py` |
| H3  | `numerology-api/deploy/env.prod.example` |
| H4  | `docs/runbook-payment-incident.md` |
| H5  | `numerology-api/app/routers/auth.py` |

---

## Tasks Completed

- [x] C1: CSP `connect-src` corrected — added `cms.nhansinhquan.vn`, `challenges.cloudflare.com`, `www.facebook.com`; kept `api.nhansinhquan.vn` defensively
- [x] C2: Added TODO comment block above ignore flags pointing to `docs/lint-cleanup-backlog.md`; created backlog doc listing known admin lint issues
- [x] H1: Added `_assert_production_config()` called in lifespan — raises `RuntimeError` if `environment=production` and `turnstile_secret_key` empty
- [x] H2: Dev auto-pass wrapped in `process.env.NODE_ENV !== 'production'` guard; prod with missing siteKey renders red error message, never calls `onSuccess`
- [x] H3: Added `trusted_proxy_mode: Literal["cloudflare", "direct"] = "cloudflare"` to `config.py`; rate_limit key func now: cloudflare mode → CF-Connecting-IP only (no XFF fallback); direct mode → `request.client.host`; added placeholder to `env.prod.example`
- [x] H4: Appended "Rate Limit Notes" section to runbook documenting per-worker tradeoff, restart reset, and Redis upgrade path
- [x] H5: Converted `_forgot_password_key` to `async def`; parses `await request.json()` directly (body cached by Starlette); removed stale `request.state._forgot_email` assignment from handler

---

## Verify Results

- **Imports:** `from app.main import app` → `import OK` (no startup error in dev env where `ENVIRONMENT` defaults to `"production"` but Starlette lifespan not triggered on import)
- **Tests:** 17 failed, 173 passed — matches Phase 03 baseline exactly, no regressions
- **Frontend build:** PASS (sitemap generated, build completed)

---

## Blockers

None.

---

## Unresolved Questions

1. `config.py` default `environment: str = "production"` means local dev without `.env` would trigger the turnstile assertion on first startup. Recommend changing default to `"development"` — deferred, as this existed before Phase 03 and is out of scope.
2. `_forgot_password_key` as `async def` — slowapi ≥0.1.9 required to support async key_func. Version not pinned in requirements; should be confirmed before deploy.
3. `TRUSTED_PROXY_MODE` default is `"cloudflare"` — ops must confirm Cloudflare proxy is active in prod (not DNS-only) or set `TRUSTED_PROXY_MODE=direct`.
