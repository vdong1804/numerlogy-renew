# Phase 01+02 Critical & High Fixes Report

**Date:** 2026-05-26
**Agent:** fullstack-developer
**Status:** COMPLETED

---

## Files Modified

| File | Changes |
|------|---------|
| `Numerology-Landing-Page/sentry.client.config.ts` | C1 + C2 |
| `Numerology-Landing-Page/sentry.server.config.ts` | C2 |
| `Numerology-Landing-Page/sentry.edge.config.ts` | C2 |
| `Numerology-Landing-Page/.env.example` | C1 — added NEXT_PUBLIC_SENTRY_DSN + SENTRY_DSN placeholders |
| `numerology-api/app/routers/my_account.py` | C3 |
| `numerology-api/app/services/fulfillment_service.py` | H1 + H5 |
| `numerology-api/app/services/upload_service.py` | H1 |
| `numerology-api/app/jobs/reconcile_sepay.py` | H2 + H3 |
| `numerology-api/app/utils/signed_url.py` | H4 |
| `numerology-api/app/routers/admin/orders.py` | H6 |

---

## Fix Summary

**C1** — `sentry.client.config.ts`: renamed `process.env.SENTRY_DSN` → `process.env.NEXT_PUBLIC_SENTRY_DSN`. Server/edge configs keep `SENTRY_DSN` (correct — Node.js can read it). `.env.example` updated with both vars.

**C2** — All 3 sentry configs: implemented real `beforeSend` PII scrubber. Strips email/phone/JWT regex from `event.message`, `event.exception.values[].value`, `event.request.data`, and `Authorization` header. Was previously a no-op returning event unchanged.

**C3** — `my_account.py:205-210`: added path traversal guard using `os.path.realpath` + `os.path.commonpath`. Resolves symlinks before comparison. Rejects with 400 if resolved path escapes `settings.media_root`.

**H1** — `fulfillment_service.py:281`: replaced `datetime.utcnow()` → `datetime.now(timezone.utc)`. `upload_service.py:53`: same fix, added `timezone` to import.

**H2** — `reconcile_sepay.py`: moved `await db.commit()` inside per-order try block (after flush). Each successful order commits independently; later failures cannot roll back already-fulfilled orders.

**H3** — `reconcile_sepay.py:76-84`: broadened idempotency check to `WHERE provider IN ('sepay','reconcile') AND status IN ('matched','received','duplicate')`. Previously only checked `status='matched'` — missed webhook-handled orders.

**H4** — `signed_url.py`: added `"typ": "report_download"` to payload in `make_signed_token`. `verify_signed_token` now rejects tokens where `typ != "report_download"`. Prevents cross-purpose token reuse.

**H5** — `fulfillment_service.py:66,392`: replaced `settings.media_url.replace("/media", "")` with `settings.frontend_url.rstrip("/")` in both order-paid and order-refund email payloads. Eliminates fragile string replacement.

**H6** — `admin/orders.py:110-121`: pre-checks order status *before* calling `refund_order`. Sets `already_refunded` flag from that snapshot. Note only appended when order was already refunded before the API call — not on every successful first refund.

---

## Verification

- **Backend imports:** `from app.main import app` → `imports OK`
- **Backend tests:** `15 failed, 175 passed` — same 15 pre-existing failures, zero regression
- **Frontend build:** `next build` + `next-sitemap` → completed successfully

---

## Deferred (Medium/Low — Phase 03/post-launch)

- fulfillment_service.py 467 LOC split
- `body: dict` password schema → Pydantic model
- reconcile early-return masks counters
- Cookie banner inline styles
- Email template fallback dead-code
- AdminOrderSummary.status missing 'refunded'
- JSON-LD placeholder email
- Footer hardcoded contact
- Sitemap lastmod year
- `hasValidConsent` naming
- `isinstance(int)` accepts bool

---

## Unresolved Questions

1. `NEXT_PUBLIC_SENTRY_DSN` — deployment env must set this separately from `SENTRY_DSN`; confirm ops team is aware.
2. `tracesSampleRate: 0.1` — confirmed acceptable for launch volume?
3. `bank_account_number` empty defaults — silently breaks QR generation in prod?
4. No tests for `signed_url.py` or `reconcile_sepay.py` — tester agent should add coverage.
