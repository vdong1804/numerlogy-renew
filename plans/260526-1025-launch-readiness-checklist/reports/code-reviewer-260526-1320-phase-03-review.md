# Code Review: Phase 03 (Security + UX + Email)

**Date:** 2026-05-26
**Reviewer:** code-reviewer subagent
**Scope:** ~25 files, ~1.3k LOC (security middleware, captcha, emails, UX pages)
**Overall Score:** **8.9 / 10** (does NOT auto-approve; 2 critical config fixes required)

---

## Critical Issues (2)

1. **`deploy/nginx.conf:95` — CSP `connect-src` whitelists wrong host.**
   Lists `https://api.nhansinhquan.vn` but actual backend per `.env`/`env.prod.example` is `cms.nhansinhquan.vn`. Browser will block ALL XHR/fetch from frontend to backend → site fully broken under CSP. Also missing `https://challenges.cloudflare.com` in `connect-src` (Turnstile JS posts there) and `https://*.facebook.com` ok but Pixel also needs `https://www.facebook.com` for `tr/`.
   Fix: change to `https://cms.nhansinhquan.vn https://challenges.cloudflare.com https://www.facebook.com`.

2. **`next.config.js:13-15` — `typescript.ignoreBuildErrors: true` still on.**
   Carryover from Phase 01 review (flagged previously). At launch this hides any new type regression in Phase 03 surface (TurnstileWidget global `window` casts, RHF generics). Severity is HIGH-borderline-CRITICAL because every subsequent change ships unchecked. Either remove the flag now or scope it to specific admin paths via a temporary `exclude` list in `tsconfig.json`.

---

## High Issues (5)

1. **`turnstile_service.py:20-23` — Fail-open in prod if env not set.**
   If `TURNSTILE_SECRET_KEY` is accidentally empty in `.env.prod`, ALL register/forgot endpoints silently bypass CAPTCHA. Add a startup assertion: when `settings.environment == "production"`, require secret key non-empty (raise at boot). Network-failure path (line 41-44) correctly fail-closed — good.

2. **`auth.py:67, 167` — Captcha verify runs INSIDE the rate-limited handler, but the order is correct.** Rate limit decorator wraps the function so it fires first; captcha call happens only after pass. Acceptable. However captcha verify also runs for the existing-user 409 path (line 70 after captcha) — fine, but DB lookup leaks email-existence timing if Turnstile is slow. Minor — flag as info only.

3. **`turnstile-widget.tsx:21,25-28` — Dev fallback risk in prod build.**
   If `NEXT_PUBLIC_TURNSTILE_SITE_KEY` is unset at build time (CI misconfig), widget auto-emits `'dev-skip-token'` and submit button enables. Backend will reject the token (good), but UX shows "[CAPTCHA disabled — dev mode]" banner publicly. Add a guard: `if (process.env.NODE_ENV === 'production' && !siteKey)` → render an error and DO NOT call `onSuccess`. Defense-in-depth.

4. **`rate_limit.py:17-23` — `X-Forwarded-For` trusted when `CF-Connecting-IP` absent.**
   Behind Cloudflare → safe. If Cloudflare proxy is switched to DNS-only (incident, migration), XFF becomes attacker-controlled and a single bad actor can rotate IPs to bypass `3/minute`. Mitigation: document that `proxy_set_header X-Real-IP $remote_addr` from nginx (line 123 ✓) should be the preferred fallback, not raw XFF. Consider `request.headers.get("X-Real-IP")` between CF header and XFF.

5. **`rate_limit.py:27-31` — In-memory storage, no Redis backend.**
   Counter resets on every uvicorn restart and is per-worker (gunicorn `-w 4` = 4 independent limits). Effective limit is `4 × 3/min = 12/min` for `register`. Acceptable for launch (low traffic) but document the limitation, or switch to `storage_uri="redis://..."` before scale-up.

---

## Medium Issues (4)

1. **`auth.py:139-148` — `_forgot_password_key` reads `request.state._forgot_email` set on line 164, but the decorator runs BEFORE the handler body.** On first call `request.state._forgot_email` is missing → key falls back to `"{ip}:unknown"`, so per-email isolation never kicks in for the first request. Mitigation: extract email via `await request.json()` inside the key_func, OR drop the email part entirely (IP-only limit is already pragma). Currently the code "works" only because `getattr(..., "unknown")` returns a consistent key.

2. **`email_outbox_service.py:50-54` — `_enrich_payload` uses `setdefault` correctly** (won't override existing `frontend_url` set by callers). Good. Verified: `fulfillment_service.py:85,392` set their own; `register/forgot` payloads don't set it → default kicks in. No bug, but the `_enrich_payload` injection is invisible at call-site — a brief docstring note "callers may pre-set frontend_url to override" would help.

3. **`Footer.tsx:21-24` — Two footer links point to `'#'`** (Kiến thức, Affiliate). Dead links in production footer. Either remove or route to `/coming-soon`.

4. **`huong-dan.tsx:108-125` — Placeholder "Ảnh minh họa" boxes** shipped to prod. Either provide real screenshots or hide the box block with a `display:none` until ready.

---

## Low / Nitpick (6)

- `auth.py:15-25` — `import logging` then `from app.schemas...` split by `logger = ...`. Reorder imports for PEP8.
- `turnstile_service.py:32` — `httpx.AsyncClient(timeout=5.0)` — 5s blocks request; consider `2.5s` (Turnstile p99 ~500ms).
- `nginx.conf:84` — HSTS `max-age=63072000` (2y) without `preload` directive but spec mentions submit later — fine; do NOT submit to preload list until 100% sure all subdomains can serve HTTPS.
- `faq.tsx:131` — Using native `<details>` (zero-dep, accessible) — different from rest-of-site MUI Accordion. Pragmatic choice; no styling consistency issue since custom sx. Acceptable.
- `order-paid.txt:15-17` — Uses `base_url` for download links but `frontend_url` for orders page. Two distinct vars set to same value in `fulfillment_service.py:85-86` — DRY violation, single var suffices.
- `welcome.txt:8`, `quota-low.txt:6`, `order-expired.txt:6` — Fallback `or 'https://nhansinhquan.vn'` is redundant since `_enrich_payload` always sets it. Harmless but noise.

---

## Edge Cases Found (Scout)

- **Turnstile timeout** → handled (fail-closed, line 41-44). ✓
- **`X-Forwarded-For` empty string** → `.split(",")[0].strip()` returns `""`, then `or` falls through to `get_remote_address`. ✓
- **Email render with `None` payload values** — e.g., `reason=None` in refund email renders as literal "None". Backend passes through `_enrich_payload` without sanitizing. Minor; refund flow always sets `reason`.
- **Rate-limit + slowapi disabled in tests** — `Limiter(enabled=False)` correctly no-ops. ✓
- **`SlowAPIMiddleware` only mounted if `rate_limit_enabled`** (main.py:102) — but `@limiter.limit()` decorators still applied to handlers. When middleware absent, decorators raise; verify with tests (slowapi raises `KeyError` on missing middleware). Worth a `tester` follow-up.

---

## Strengths

- Clean separation: `rate_limit.py`, `turnstile_service.py` each <50 LOC, single responsibility.
- Email outbox correctly uses `with_for_update(skip_locked=True)` for concurrent workers.
- Plain-text email fallback (`render_text_template`) wired into multipart properly via `_html_to_text` rough strip.
- Turnstile widget cleanup (`delete window[callback]`) prevents memory leak on unmount.
- `EmptyState` + skeleton components are clean, reusable, no dependencies on parent context.
- Security headers (`always` directive present on all `add_header` ✓), HSTS 2y safe choice.
- CSP includes `'unsafe-inline'`/`'unsafe-eval'` with TODO comment — pragmatic, deferrable.

---

## Top 5 Recommended Actions

1. **[CRITICAL]** Fix `nginx.conf` CSP `connect-src` → replace `api.nhansinhquan.vn` with `cms.nhansinhquan.vn`, add `challenges.cloudflare.com` + `www.facebook.com`.
2. **[CRITICAL]** Remove or scope `typescript.ignoreBuildErrors` in `next.config.js`.
3. **[HIGH]** Add startup assertion in `config.py`: if `environment=="production"` then `turnstile_secret_key` required.
4. **[HIGH]** Add prod guard in `turnstile-widget.tsx:25` — block dev-skip path when `NODE_ENV==="production"`.
5. **[MEDIUM]** Fix `_forgot_password_key`: extract email via `await request.json()` or remove email component from key.

---

## Unresolved Questions

1. Cloudflare deployment: is the site actually fronted by Cloudflare in prod, or direct nginx? If direct nginx, the `CF-Connecting-IP` header is attacker-spoofable and rate-limit is bypassable. Confirm with ops.
2. Is `cms.nhansinhquan.vn` the only backend host, or is there a separate `api.nhansinhquan.vn` planned? CSP fix depends on the answer.
3. Should `SlowAPIMiddleware` always be mounted (even when `rate_limit_enabled=false`) since `Limiter(enabled=False)` already no-ops? Current code may break decorated routes in test env.
