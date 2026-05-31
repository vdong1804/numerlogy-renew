# Phase 05 Code Review

## Summary
- Overall: **pass with required fixes** — ship-blocker is the SePay webhook bypass (C1). Everything else is fixable in-session or post-merge.
- Critical: 4
- High: 7
- Medium: 9
- Low: 6

## Critical

### C1. SePay webhook does NOT call `approve_payment` — chat addons never auto-fulfilled
**File:** `numerology-api/app/services/sepay_service.py:159` + `numerology-api/app/routers/chat/addons.py:93-100`
**Issue:** `addons.py` purchase endpoint creates a **UserPayment** row (status=1). SePay webhook (`process_webhook`) only knows about **Order** rows — it locks `Order` by `ref_code`, marks it paid, and calls `fulfillment_service.fulfill_order(db, order)`. `approve_payment` (the only branched dispatcher) is called ONLY from `app/routers/admin/payments.py:61` (manual admin approval) and nowhere else. A user paying via SePay for a chat addon will:
1. POST `/api/chat/addons/{id}/purchase` → UserPayment row created, bank info returned
2. User transfers money with content `CHATADDON{payment_id}` (no `NSQ-XXXXXXXX` ref_code anywhere)
3. SePay webhook fires → `parse_ref_code` returns None → event marked `unmatched` → no Order found → addon NEVER fulfilled

Step 2 report acknowledged the file choice (point 3) but did not flag that chat addon now has **NO webhook fulfillment path** — only manual admin approval works. Spec said "reuse existing payment flow (SePay webhook or manual)". `fulfill_chat_addon` is correct, but unreachable from a real bank transfer until an admin clicks "approve".
**Fix:** Add a SePay matcher branch: parse `CHATADDON<payment_id>` from `payload.content`, lock `UserPayment` by id, validate `status=1` + amount, call `approve_payment(db, payment_id)`. Minimal diff, matches admin path semantically.

### C2. Stream path can deliver a free message on client disconnect after assistant commit
**File:** `numerology-api/app/routers/chat/_stream_generator.py:98-106`
**Issue:** Sequence is `await db.commit()` (line 98) → `QuotaService(db).decrement(...)` (line 102) → yield citations/done. After `commit()`, a NEW transaction starts. If the client disconnects between line 98 and the next commit, the assistant message is durably persisted but the decrement is rolled back (`app/deps.py:25-27` rolls back on exception). User receives complete LLM answer for free, repeatable indefinitely.
**Fix:** Move `decrement` BEFORE `db.commit()` so both land in one transaction (matches sync-path pattern at messages.py:146-158). Replace lines 88-106:
```python
asst_msg = await persist_assistant_message(...)
try:
    await QuotaService(db).decrement(conv.user_id, decision)
except QuotaConflictError:
    logger.warning(...)
await db.commit()
```

### C3. Admin-form chat_addon validates client-side only — backend accepts message_count=0/null
**File:** `numerology-api/app/schemas/package.py:55-72` + `numerology-api/app/services/chat/addon_fulfillment.py:47-52`
**Issue:** `PackageCreate.message_count: Optional[int] = None` has NO `ge=1` or required-when-kind=chat_addon validation. Admin can POST `{"package_kind":"chat_addon","message_count":0}` and the row is created. `fulfill_chat_addon` then raises `ValueError` at payment-approval time — AFTER the user paid, leaving an approved payment with no granted addon. Frontend zod catches this in UI; any API client (curl, mobile, broken form) bypasses it.
**Fix:** Add pydantic `model_validator(mode="after")` on `PackageCreate` + `PackageUpdate`:
```python
@model_validator(mode="after")
def _validate_chat_addon_fields(self):
    if self.package_kind == "chat_addon":
        if self.message_count is None or self.message_count < 1:
            raise ValueError("message_count required (>=1) when package_kind='chat_addon'")
        if self.tier is None:
            raise ValueError("tier required when package_kind='chat_addon'")
        if self.validity_days is None or self.validity_days < 1:
            raise ValueError("validity_days required (>=1) when package_kind='chat_addon'")
    return self
```

### C4. `.prettierrc.json` newly added at repo root conflicts with existing team setup
**File:** `Numerology-Landing-Page/.prettierrc.json` (NEW)
**Issue:** Repo already had `prettier@^2.7.1` installed and `eslint-config-prettier` configured (package.json lines 107, 114, 125) — but NO `.prettierrc.json` previously existed, meaning team used defaults (double quotes, semis on). New file forces `singleQuote: true, semi: false`:
- Reformats every file the next time anyone runs `next lint --fix` or `prettier --write`
- Breaks consistency with all existing committed code (double quotes + semis)
- Added silently by Step 3 admin work to match react-hook-form scaffolding style
**Fix:** Delete the file. Existing code stays untouched; admin files would re-format only if the team intentionally adopts this config.

## High

### H1. Race condition on `check()` → `decrement()` window: a SECOND concurrent request bypasses lock
**File:** `numerology-api/app/services/chat/quota_service.py:79-117`
**Issue:** `check()` does a plain `SELECT` (no FOR UPDATE) called from `_check_quota_or_402` BEFORE the LLM. Two concurrent requests both see remaining=1, both pass check, both fire LLM (~30s each), both attempt decrement. SELECT FOR UPDATE inside `_decrement_addon` serializes the second — sees remaining=0 → raises `QuotaConflictError`. Router swallows the error (`logger.warning`, ignored) and returns the reply. Result: 2 messages spent for 1 paid slot.

Free path: no lock at all — `INSERT … ON CONFLICT` atomic at row level, but the `check()` saw the same `free_used`. 4 concurrent requests when free_used=2 can all pass check, all run LLM, all increment to 6. User pays nothing for 4 LLM calls.
**Fix:** Either (a) reserve-then-release: decrement INSIDE the same transaction as check, refund on LLM failure; or (b) on `QuotaConflictError` in stream/sync paths, log AND emit error to user (don't silently deliver).

### H2. `onQuotaExceeded` callback identity changes every render
**File:** `Numerology-Landing-Page/src/modules/chat/ChatLayout.tsx:67-69`
**Issue:** `useChatStream(activeConvId, handleMessageComplete, { onQuotaExceeded: () => setUpsellOpen(true) })` — options object and arrow function fresh every render. `useChatStream` destructures `onQuotaExceeded` (line 50) but does NOT include it in `send`'s useCallback deps (line 253: `[convId, scheduleFlush, onMessageComplete]`). `send` closure captures the FIRST `onQuotaExceeded`. Works today because `setUpsellOpen` is stable from React — latent bug for any handler that closes over component state.
**Fix:** (a) Include `onQuotaExceeded` in `send` deps; (b) Stabilize in ChatLayout: `const handleQuotaExceeded = useCallback(() => setUpsellOpen(true), [])`; or (c) Store in a ref inside the hook.

### H3. No payment-status polling after addon purchase → user has no UI feedback of fulfillment
**File:** `Numerology-Landing-Page/src/pages/chat/upgrade.tsx:73-92` + `src/modules/chat/parts/UpsellModal.tsx:72-85`
**Issue:** Purchase returns bank info and waits passively. After user transfers + webhook fires (assuming C1 fixed) + addon is granted, frontend has no detection — `refreshQuota` only fires when UpsellModal closes (ChatLayout.tsx:231-234). On `/chat/upgrade` page NO `refreshQuota` at all. User must navigate away and back.
**Fix:** 5-10s polling of `getQuota()` while `purchaseInfo` set; stop when `addon_remaining > 0`; show success toast.

### H4. SSE quota_exceeded mid-stream never reaches the UI as an event
**File:** `numerology-api/app/routers/chat/_stream_generator.py:103-106`
**Issue:** Quota check fires 402 BEFORE StreamingResponse opens (messages.py:203). If addon `remaining_messages` drops to 0 between check and decrement (parallel request, admin action, tampering), `QuotaConflictError` is silently logged, user already got full LLM reply. SSE `error` payload with `code: "quota_exceeded"` (handled in `use-chat-stream.ts:196-201`) is plumbed but the server never emits it. Upsell modal does NOT fire for this edge case.

Counter to H1: manifests as a "free" message rather than a missed upsell, but the SSE contract advertises the event. Spec accepted in risk table.
**Fix:** On `QuotaConflictError`, emit `sse_event("error", {"code": "quota_exceeded_postcommit", ...})` before yielding `done`.

### H5. `PackageOut.model_validate` on existing pdf_download row works ONLY because of default
**File:** `numerology-api/app/schemas/package.py:25-28`
**Issue:** `package_kind: PackageKind = "pdf_download"` — with `from_attributes=True`, pydantic reads SQLAlchemy attribute. Default does NOT apply when attribute exists but is None. Migration adds column with `server_default="pdf_download"` so safe in normal flow — fragile for raw SQL inserts, DB import scripts, or downgrade scenarios.
**Fix:** `package_kind: Optional[PackageKind] = "pdf_download"` OR add coercing validator. Low-risk to leave; flag.

### H6. Quota counter uses UTC date — Asia/Bangkok users reset at 07:00 local
**File:** `numerology-api/app/services/chat/quota_service.py:67-68, 156-200`
**Issue:** Confirmed: `_utc_today()` returns `datetime.now(timezone.utc).date()`. UTC+7 users see reset at 07:00 wall-clock. Spec risk table explicitly accepts ("Use server UTC date consistently").
**Fix:** None — accepted. Document in UI tooltip ("Hết hạn vào 07:00 sáng theo giờ Việt Nam").

### H7. Backend `tier` Literal is case-sensitive — admin form OK, legacy data risk
**File:** `numerology-api/app/schemas/package.py:11`
**Issue:** `AddonTier = Literal["flash", "pro"]` — case-sensitive. Admin form NativeSelect emits lowercase, so safe. Any seed script writing `"Pro"` fails PackageOut on read.
**Fix:** Add lower() validator or document. No active bug.

## Medium

### M1. `messages.py` is 212 LOC (12 over limit)
**File:** `numerology-api/app/routers/chat/messages.py`
**Fix:** Extract sync happy-path to `_run_sync_turn`. Optional.

### M2. `_stream_generator.py:102` instantiates new `QuotaService(db)` redundantly
**File:** `numerology-api/app/routers/chat/_stream_generator.py:102`
**Fix:** Inject QuotaService into `generate_sse_events` signature. Trivial.

### M3. Empty addon list test seeds a PDF package but assertion is a tautology
**File:** `numerology-api/tests/routers/chat/test_addons.py:87-99`
**Issue:** `assert all(p.get("tier") is not None or True for p in data)` — `x or True` always True.
**Fix:** `assert not any(p["name"] == "PDF Only" for p in data)`.

### M4. No test for purchase race (two parallel `/purchase` for same package)
**File:** `numerology-api/tests/routers/chat/test_addons.py`
**Issue:** Both 201s create two pending UserPayment rows — accepted for VND, but undocumented.
**Fix:** Document or add test.

### M5. No test for decrement-after-expiration during a long stream
**File:** `numerology-api/tests/services/chat/test_quota_service.py`
**Issue:** `_decrement_addon` works by `addon_id` only, doesn't re-check `expires_at`. Captured-id can be decremented past expiry. Harmless but inconsistent.
**Fix:** Validate `expires_at` in `_decrement_addon` and raise QuotaConflictError; add test.

### M6. AddonList in UpsellModal shows ALL packages, not 3 — spec said "3 options"
**File:** `Numerology-Landing-Page/src/modules/chat/upgrade/AddonList.tsx`
**Issue:** Spec line 184. Current implementation unlimited. `max-h-72 overflow-y-auto` mitigates.
**Fix:** Add `limit?: number` prop; pass `limit={3}` from UpsellModal. Or accept current behavior.

### M7. Simultaneous purchase clicks on different cards racy
**File:** `Numerology-Landing-Page/src/pages/chat/upgrade.tsx:73-92`
**Issue:** First sets `purchasingId=cardA`, click cardB overwrites mid-flight; cardA returns and clobbers state.
**Fix:** Disable all buttons when `purchasingId !== null`, not just self-match. AddonCard.disabled prop already correct; click handler isn't blocked at page level.

### M8. `bank_code` field returned but never displayed
**File:** UpsellModal.tsx + upgrade.tsx
**Issue:** Backend returns `bankCode` but neither view renders it; users can't build VietQR.
**Fix:** Display in InfoRow grid or drop from schema (KISS).

### M9. `payment_id` content prefix `CHATADDON{id}` is undocumented — SePay can't match
**File:** UpsellModal.tsx:139 + upgrade.tsx:166
**Issue:** Frontend shows user `Nội dung CK: CHATADDON{paymentId}`; backend SePay matcher only parses `NSQ-XXXXXXXX` (sepay_service.py:33). User-facing manifestation of C1.
**Fix:** Same as C1 — generate `NSQ-` ref_code per UserPayment OR extend matcher.

## Low / Nits

- `app/routers/chat/addons.py:62` — `# noqa: E501` on a decorator that's not even long. Remove.
- `app/schemas/chat/addon.py:1` — `# ruff: noqa: UP045, UP017` claims both required; only UP017 is. Tighten.
- `_stream_generator.py:25` — import line could be alphabetized for ruff I001.
- `package-form-schema.ts:74-77` — eslint-disable could be file-level for entire snake_case schema.
- `QuotaBadge.tsx:32` — `TIER_STYLES[pkg.tier] ?? TIER_STYLES.flash` triggers noUncheckedIndexedAccess.
- Vietnamese consistency: "Hết lượt" / "Hết lượt nhắn tin" / "Đã hết lượt miễn phí" — three phrasings for same state. Pick one.

## Strengths

1. **Idempotent fulfillment correctly implemented** — `fulfill_chat_addon` checks `payment_id` uniqueness BEFORE inserting, and `approve_payment` rejects status!=1. Two layers of defense, both tested.
2. **Quota decrement only after persist+commit (stream)** — even with C2 flag, principle is right: don't bill for failed turns.
3. **Pydantic schema extensions** minimal and backward-compatible — PDF flow unaffected.
4. **Test coverage solid for happy paths**: 12 QuotaService unit + 9 addons router + 5 quota endpoint + 4 fulfillment + 5 messages/stream quota = +35 new tests.
5. **SELECT FOR UPDATE on addon decrement** correctly implemented (line 172). Race test acknowledges SQLite limitation and TODO'd for Postgres validation.
6. **UTC consistency** — `datetime.now(timezone.utc)` everywhere, no naive timestamps.
7. **Frontend SSE quota_exceeded 402 branch** has explicit `body.detail.code` check — generic 402s won't accidentally trigger upsell.
8. **Admin form conditional rendering via useWatch** is clean — `number_download` hides for chat_addon, addon fields hide for pdf_download, `preparePayload` strips irrelevant keys.
9. **`addons.py` returns 400 (not 404) on wrong package_kind** — distinguishes "doesn't exist" from "wrong type".
10. **No new prod deps added** — react-hook-form, zod, @hookform/resolvers all already present.

## Test coverage gaps

- No test for SePay webhook → chat_addon path (because C1 — path doesn't exist).
- No test asserting `_stream_generator.py` rolls back decrement on client disconnect (C2).
- No test for `PackageCreate` rejecting `message_count=0` when `package_kind=chat_addon` (C3 — no backend validator yet).
- No frontend integration test for `onQuotaExceeded` callback identity (H2).
- No end-to-end purchase→quota-refresh test on `/chat/upgrade` (H3).
- M5: no test for decrement on already-expired addon.
- Race test tolerates SQLite no-op SELECT FOR UPDATE — must run against Postgres in CI to validate true safety (TODO comment present).

## Unresolved questions

1. **C1 fix path** — replace UserPayment with Order for chat addons (heavier, unifies fulfillment), or extend SePay matcher with `CHATADDON<id>` prefix (lighter, two parallel flows)? Recommend the latter; flag tech debt.
2. **C2 fix vs commit-twice** — single-commit (atomic decrement + assistant_message) acceptable, or do you want assistant message durable even if decrement somehow fails?
3. **H1 reserve-then-release** — willing to take 2-3ms extra latency on `check` for safety, or accept rare double-spend? Low risk for free 3/day; higher for addon with 1 remaining + Pro tier.
4. **C4 prettier** — was new `.prettierrc.json` intentional from admin agent or accidentally committed?
5. **M9** — should user-visible bank "Nội dung CK" reuse `NSQ-` ref_code system, or have separate chat-addon prefix? Affects C1 fix shape.
