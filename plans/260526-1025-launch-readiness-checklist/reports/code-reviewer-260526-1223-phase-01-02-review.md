# Code Review: Phase 01 (Frontend) + Phase 02 (Backend)

**Date:** 2026-05-26
**Reviewer:** code-reviewer subagent
**Scope:** ~30 files, ~2.5k LOC
**Overall Score:** **8.7 / 10** (does NOT auto-approve; minor fixes needed)

---

## Critical Issues (3)

1. **`sentry.client.config.ts:9` — Client DSN must use `NEXT_PUBLIC_` prefix.**
   `process.env.SENTRY_DSN` is undefined in browser bundles. Sentry never initializes client-side.
   Fix: rename env var to `NEXT_PUBLIC_SENTRY_DSN` (server/edge can keep `SENTRY_DSN`).

2. **`sentry.{client,server,edge}.config.ts:23-27` — `beforeSend` is a no-op.**
   Comment says "Strip PII" but function returns `event` unchanged. Email/phone/JWT in breadcrumbs will leak to Sentry.
   Fix: scrub `event.request.headers.authorization`, `event.user.email`, regex-strip emails/phone from `event.message` and breadcrumb strings.

3. **`my_account.py:204-206` — Token download skips ownership re-check after path-1 success.**
   Token alone authorizes — fine by design — but combined with `report.user_id is None` (lead-magnet pre-signup case is theoretical), there's no defense-in-depth. Lower-impact but worth a `report.user_id is not None` guard.
   Also `pdf_path.startswith("REFUNDED/")` check works for refunded files, but a manually corrupted DB row (`pdf_path = "../etc/passwd"`) would only be blocked by the `os.path.isfile` check, not by path traversal validation. Recommend `os.path.commonpath([abs_path, settings.media_root]) == settings.media_root`.

---

## High Issues (6)

1. **`fulfillment_service.py:281` — `datetime.utcnow()` deprecated in Py3.12.**
   Use `datetime.now(timezone.utc)`. Same issue at `upload_service.py:53`.

2. **`reconcile_sepay.py:129` — Single `commit` after loop = all-or-nothing.**
   If one order errors then commits via rollback inside the loop, the outer commit may fail. Per-order `await db.commit()` after each successful fulfill would be safer (current code can lose all matches if a late-loop exception fires).

3. **`reconcile_sepay.py:76-83` — Idempotency check queries by `status="matched"` only.**
   If webhook landed `status="received"` then crashed, reconcile will re-fulfill. Should also check `WebhookEvent.order_id == order.id AND status IN ('matched','received','duplicate')` — or check `Order.status != 'pending'` first (the `with_for_update` lock at line 87 catches this, but it's fragile).

4. **`signed_url.py:36` — No token type/nonce in payload.**
   `{user_report_id, exp}` — a token signed for report download could theoretically be replayed if the same secret is reused for another HMAC use case later. Add `"typ": "report_dl"` to payload + verify; cheap insurance.

5. **`fulfillment_service.py:66` — `base_url = settings.media_url.replace("/media", "")` is fragile.**
   If `media_url = "https://cdn.example.com/media-cache/media"`, replace strips too much. Should use `settings.frontend_url` directly (already exists in config.py:31).

6. **`admin/orders.py:117` — `note` logic always evaluates `order.status == "refunded"` after a successful refund.**
   So `_note: "already refunded"` is set on every refund call — even the first one. Fix: return `note` only when service detected pre-existing refund (service could return a tuple `(order, was_already_refunded)`).

---

## Medium Issues (7)

1. **`fulfillment_service.py` is 467 LOC — exceeds 200 LOC guideline.**
   Split: extract `refund_*` helpers + `_render_report_pdf` into `fulfillment/refund.py` and `fulfillment/pdf.py`.

2. **`my_account.py:230` — `body: dict` for password change.**
   Use a `PasswordChangeRequest(BaseModel)` for validation + OpenAPI docs.

3. **`reconcile_sepay.py:42` — `if not transactions: return counters` aborts even on legitimate empty windows.**
   Counters never reach DB-checking code; pending orders are silently skipped. Restructure to always run the order query so admin can see "checked=N, matched=0".

4. **`sepay_service.py:115` — Triple `or` parsing chain is unreadable.**
   Refactor: list comprehension over `[content, description, referenceCode]` with `next((r for r in ... if r), None)`.

5. **`cookie-consent.tsx` — Inline styles instead of MUI/Emotion.**
   Project uses MUI + emotion (per `_app.tsx`). Justified by note in code, but inconsistent with codebase. Low cost to migrate.

6. **`order-paid.html:15` — Link template assumes `r.name` truthy or falls back to `'Báo cáo #' ~ r.report_id`.**
   The Python side at `fulfillment_service.py:71` always sends `"name": f"Báo cáo #{r.id}"` so the fallback never fires (and is wrong Python interpolation in Jinja2 — `~` is string concat). Cleanup: just use `{{ r.name }}`.

7. **`admin-dashboard-api.ts:34` — `AdminOrderSummary.status` enum missing `'refunded'`.**
   Backend now returns `'refunded'`; frontend type will type-error. Add to union.

---

## Low / Nitpicks (5)

- `_document.tsx:21` — `email: '[EMAIL HỖ TRỢ]'` placeholder shipped to production JSON-LD. Replace before launch.
- `Footer.tsx:191-219` — Hardcoded placeholder address/phone/email. Replace per legal review.
- `next-sitemap.config.js:25-28` — `lastmod: '2025-05-26'` (year off vs current 2026 date). Use ISO from build env.
- `consent-storage.ts:46` — `hasValidConsent` returns bool but rejected consent (`{analytics:false,marketing:false}`) is still "valid". Naming OK semantically, but consider renaming to `hasConsentRecord` for clarity.
- `signed_url.py:64` — `isinstance(user_report_id, int)` accepts `bool` (Python quirk: `True isinstance int`). Add `not isinstance(user_report_id, bool)`.

---

## Strengths

- **Excellent idempotency design** on SePay webhook + reconcile (UNIQUE constraint + `with_for_update` row lock).
- **HMAC token verify uses `hmac.compare_digest`** — constant-time, correct.
- **Refund is idempotent** + reverses quota with `max(0, ...)` floor.
- **Migration 0008** is reversible (drop+recreate constraint, both directions).
- **Consent banner correctly gates analytics** — `Analytics` component only injects scripts after `getConsent().analytics === true`.
- **Refund email + signed download links** are well-templated with both HTML + plain-text variants.
- **Robots.txt + sitemap exclusions** correctly hide admin/checkout from crawlers.

---

## Recommended Actions per Phase

### Phase 01 (Frontend)
1. Fix `NEXT_PUBLIC_SENTRY_DSN` env var rename (Critical #1).
2. Implement actual PII scrubbing in `beforeSend` (Critical #2).
3. Add `'refunded'` to `AdminOrderSummary.status` union (Medium #7).
4. Replace `[EMAIL HỖ TRỢ]` placeholder in `_document.tsx` JSON-LD.
5. Update `lastmod` in `next-sitemap.config.js` from build-time env.

### Phase 02 (Backend)
1. Replace `datetime.utcnow()` with `datetime.now(timezone.utc)` (2 sites).
2. Use `settings.frontend_url` instead of `media_url.replace("/media", "")` (3 sites in `fulfillment_service.py`).
3. Add `"typ": "report_dl"` to signed token payload + verify.
4. Strengthen reconcile idempotency check to include all webhook_events for the order_id.
5. Restructure `reconcile_sepay.run()` to commit per-order, not batch.
6. Fix `_note: "already refunded"` always-true bug in admin refund endpoint.
7. Modularize `fulfillment_service.py` (>200 LOC).

---

## Unresolved Questions

1. **Sentry sample rate `tracesSampleRate: 0.1`** — confirmed acceptable for launch volume?
2. **`bank_account_number` etc. in config** — are these set in production env? Empty defaults will silently break QR generation.
3. **Refund email template at line 13:** "3–5 ngày làm việc" — does this match actual SePay refund SLA? Legal/CS sign-off needed.
4. **Lead-magnet pre-signup signed token flow** — not exercised in current code; verify `report.user_id` is always non-null at download time.
5. **No tests for `signed_url.py` or `reconcile_sepay.py`** observed — confirm with tester agent.
