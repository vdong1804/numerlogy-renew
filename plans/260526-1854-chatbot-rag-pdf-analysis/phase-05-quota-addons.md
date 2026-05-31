# Phase 05 — Quota + Add-on Packages + Payment Integration

## Context Links
- Depends on: P2 (chat endpoint), P4 (UI for upsell)
- Existing models: `app/db/models/package.py`, `app/services/payment_service.py`, `app/services/fulfillment_service.py`
- Brainstorm: §4.4 add-on schema, §4.3 quota check step

## Overview
- **Priority:** Critical (revenue mechanism)
- **Status:** complete (2026-05-28)
- **Duration:** 2 weeks
- **Description:** Enforce free 3 msg/day for registered users, sell add-on packages (extra messages + Pro tier), integrate with existing payment flow (UserPayment + manual approval or SePay webhook).

## Key Insights
- Reuse existing `UserPayment` flow — add `package_type` field or use existing `Package` with new metadata.
- Daily reset: handled at query time (`WHERE date = CURRENT_DATE`) — no scheduled job needed.
- Tier resolution priority: active addon (Pro) > free quota (Flash).
- Addon balance decremented atomically (SELECT FOR UPDATE) to prevent race.
- Free 3/day applies even after addon depletes (keeps users engaged).

## Requirements

### Functional
- Add `package_kind` column to `packages`: enum (`pdf_download`, `chat_addon`).
- `chat_addon` packages have: `message_count` (e.g. 100), `tier` (pro/flash), `validity_days` (30).
- New table `chat_addon_purchases` tracks balance per user.
- POST `/api/chat/addons/{package_id}/purchase` initiates payment (reuse SePay/manual flow).
- After payment approved → `fulfillment_service` creates `ChatAddonPurchase` row.
- Quota check middleware (function): determine tier + can_send + remaining.
- GET `/api/chat/quota` returns current free remaining + addon balance.
- Frontend: upsell modal when quota exceeded, addon listing on `/chat/upgrade`.

### Non-Functional
- Quota check <50ms (in-process DB query, no LLM call yet).
- Addon balance decrement atomic (transaction + row lock).
- Payment webhook idempotent (existing pattern).

## Architecture

```
app/
├── db/models/chat/
│   ├── chat_addon_package.py   # Or reuse Package with package_kind
│   └── chat_addon_purchase.py
├── services/chat/
│   ├── quota_service.py        # check + decrement + balance
│   └── addon_fulfillment.py    # webhook hook for chat_addon purchase
├── routers/chat/
│   ├── addons.py               # list packages + initiate purchase
│   └── quota.py                # GET current balance
alembic/versions/
└── 0012_chat_addons.py
```

### Frontend
```
Numerology-Landing-Page/src/modules/chat/
├── upgrade/
│   ├── AddonList.tsx
│   ├── AddonCard.tsx
│   └── PurchaseFlow.tsx        # reuse existing checkout component
├── QuotaBadge.tsx              # header indicator
└── UpsellModal.tsx             # shown when quota exhausted
```

## SQL Schema (alembic 0012)

```sql
-- Differentiate package types
ALTER TABLE packages ADD COLUMN package_kind VARCHAR(30) NOT NULL DEFAULT 'pdf_download';
ALTER TABLE packages ADD COLUMN message_count INT;
ALTER TABLE packages ADD COLUMN tier VARCHAR(20);  -- 'flash' | 'pro'
ALTER TABLE packages ADD COLUMN validity_days INT;
CREATE INDEX packages_kind_idx ON packages(package_kind);

CREATE TABLE chat_addon_purchases (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  package_id BIGINT NOT NULL REFERENCES packages(id) ON DELETE RESTRICT,
  remaining_messages INT NOT NULL,
  tier VARCHAR(20) NOT NULL,
  purchased_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  expires_at TIMESTAMPTZ NOT NULL,
  payment_id BIGINT REFERENCES user_payments(id) ON DELETE SET NULL,
  is_active BOOLEAN NOT NULL DEFAULT TRUE
);
CREATE INDEX chat_addon_user_active_idx
  ON chat_addon_purchases(user_id, is_active, expires_at) WHERE is_active = TRUE;
```

## Quota Resolution Logic

```python
async def resolve_tier_and_check(user_id) -> QuotaDecision:
    # 1. Find active addon (is_active, not expired, remaining > 0)
    addon = await get_active_addon(user_id)
    if addon:
        return QuotaDecision(can_send=True, tier=addon.tier, source="addon", addon_id=addon.id)

    # 2. Check daily free quota
    used = await get_today_free_used(user_id)  # chat_quota_usage
    if used < FREE_DAILY_LIMIT:  # 3
        return QuotaDecision(can_send=True, tier="flash", source="free", free_remaining=FREE_DAILY_LIMIT-used)

    # 3. Quota exhausted
    return QuotaDecision(can_send=False, reason="quota_exceeded")
```

## Related Code Files

### Create
- `app/db/models/chat/chat_addon_purchase.py`
- `app/services/chat/quota_service.py` (≤180 LOC)
- `app/services/chat/addon_fulfillment.py` (≤100 LOC)
- `app/routers/chat/addons.py` (≤120 LOC)
- `app/routers/chat/quota.py` (≤60 LOC)
- `app/schemas/chat/addon.py`
- `alembic/versions/0012_chat_addons.py`
- `tests/services/chat/test_quota_service.py`
- `tests/routers/chat/test_addons.py`
- Frontend: `AddonList.tsx`, `AddonCard.tsx`, `QuotaBadge.tsx`, `UpsellModal.tsx`

### Modify
- `app/db/models/package.py` — add `package_kind`, `message_count`, `tier`, `validity_days`
- `app/services/fulfillment_service.py` — branch on `package_kind`: chat_addon → call `addon_fulfillment.fulfill`
- `app/routers/chat/messages.py` — call `QuotaService.check_and_decrement` before LLM
- `app/services/chat/llm_service.py` — accept `tier` param → select Flash/Pro model
- `app/services/chat/retrieval_service.py` — top-k by tier (3 free / 8 paid)
- Admin Next.js: package CRUD form adds `package_kind` selector

## Implementation Steps

1. **Alembic 0012**
   - Add columns to `packages`. Default existing rows to `pdf_download`.
   - Create `chat_addon_purchases`.

2. **Package model update**
   - Add optional fields. Backward compatible.

3. **Seed addon packages** (script or admin manual)
   - Basic: 50 msgs Pro, 30d, 49,000 VND
   - Standard: 150 msgs Pro, 30d, 119,000 VND
   - Premium: 500 msgs Pro, 60d, 349,000 VND

4. **Quota service**
   ```python
   class QuotaService:
       async def check(user_id) -> QuotaDecision
       async def decrement(decision: QuotaDecision)  # write usage or decrement addon
       async def get_balance(user_id) -> QuotaBalance
   ```
   - `check + decrement` in single transaction with SELECT FOR UPDATE on addon row.
   - `decrement` for free tier inserts/updates `chat_quota_usage`.

5. **Messages router integration**
   ```python
   # Before retrieval/LLM:
   decision = await quota.check(user.id)
   if not decision.can_send:
       raise HTTPException(402, detail={"code": "quota_exceeded", "upsell": True})
   # ... do LLM call ...
   await quota.decrement(decision)  # only after successful response
   ```

6. **Fulfillment integration**
   - In `fulfillment_service.fulfill_payment(payment_id)`:
     ```python
     pkg = payment.package
     if pkg.package_kind == "chat_addon":
         await addon_fulfillment.create_purchase(user_id, pkg, payment_id)
     else:
         # existing pdf_download logic
     ```
   - `addon_fulfillment` inserts `ChatAddonPurchase` row with `remaining_messages=pkg.message_count`, `expires_at=NOW()+validity_days`.

7. **Routers**
   - `GET /api/chat/addons` — list active `chat_addon` packages.
   - `POST /api/chat/addons/{id}/purchase` — same flow as PDF purchase (creates `UserPayment` pending → returns SePay QR or bank info).
   - `GET /api/chat/quota` — return decision + balance for UI badge.

8. **Frontend**
   - `QuotaBadge` in `/chat` header: shows "3/3 free" or "47 Pro" depending on source.
   - `UpsellModal`: triggered on 402 response — list 3 addon options + "Buy now" CTA.
   - `/chat/upgrade` page: full addon listing with prices.
   - Reuse existing checkout payment flow (SePay QR).

9. **Admin UI update**
   - Package create form: `package_kind` dropdown; when `chat_addon` selected, show extra fields (message_count, tier, validity_days).

10. **Cron: deactivate expired addons** (optional optimization)
    - Or rely on `WHERE expires_at > NOW()` filter at query time (simpler).

11. **Tests**
    - Quota service: 3 sends → 4th blocked.
    - Addon active: bypasses free counter, decrements addon.
    - Expired addon: ignored, falls back to free.
    - Concurrent decrement: 10 parallel requests with 1 remaining → only 1 succeeds.

## Todo List

- [x] Write alembic 0012 migration
- [x] Update Package model with new fields
- [ ] Seed 3 addon packages on staging (Basic/Standard/Premium) — deferred
- [x] Implement `chat_addon_purchase.py` model
- [x] Implement `quota_service.py` (check, decrement, balance)
- [x] Implement `addon_fulfillment.py`
- [x] Wire `fulfillment_service` to branch on package_kind
- [x] Add quota check to `messages.py` router (both stream + non-stream)
- [x] Update `llm_service` + `retrieval_service` to accept tier
- [x] Implement `routers/chat/addons.py` + `quota.py`
- [x] Build `QuotaBadge` component
- [x] Build `UpsellModal` component
- [x] Build `/chat/upgrade` page with AddonList
- [x] Update admin package form with `package_kind` selector
- [x] Write quota service unit tests (concurrent decrement)
- [x] Write integration test: purchase → fulfill → send msg uses addon
- [ ] Manual test: exhaust free → see upsell modal → buy addon → confirm Pro answers — deferred
- [x] Update `docs/project-overview-pdr.md` with new package kind

## Completion Notes

**Execution Summary:**
Phase 05 completed 2026-05-28. Backend foundation (Step 1), integration (Step 2), and frontend (Step 3) all delivered with 290 passing tests, zero failures. Post-review code fixes applied; critical issues resolved.

**Deliverables by Report:**
1. `fullstack-260528-0930-phase-05-step1-backend.md` — Alembic 0012, Package model, ChatAddonPurchase, QuotaService, 12 unit tests
2. `fullstack-260528-1000-phase-05-step2-backend.md` — Addon schemas, fulfillment integration, payment routing, quota wiring (send + stream), 23 tests
3. `fullstack-260528-1030-phase-05-step3-frontend.md` — QuotaBadge, UpsellModal, /chat/upgrade, AddonList, use-quota hook, ChatLayout wired
4. `fullstack-260528-1030-phase-05-step3-admin.md` — package_kind selector, conditional addon fields, shared zod schema, preparePayload helper
5. `code-review-260528-1100-phase-05.md` — 4 critical + 7 high + 9 medium + 6 nit issues; 4 criticals fixed, selected highs addressed
6. `fullstack-260528-1130-phase-05-backend-fixes.md` — SePay webhook CHATADDON matcher, stream decrement pre-commit, model validators, .prettierrc deletion
7. `fullstack-260528-1130-phase-05-frontend-fixes.md` — SSE quota_exceeded_postcommit event, onQuotaExceeded callback, quota polling + toast, card disable states

**Deviations from Plan:**
- `Package.is_active` field does not exist; addon listing filters on `expires_at > NOW()` instead (simpler, no migration needed)
- `fulfillment_service` integration done in `payment_service.py` (actual call site for package fulfillment)
- SePay webhook content matcher extended to recognize `CHATADDON{payment_id}` prefix for chat addon fulfillment
- SSE error event type `quota_exceeded_postcommit` added to signal rare post-commit race (H1)
- `.prettierrc.json` removed due to team tooling conflict

**Code Quality:**
- tsc (TypeScript) — clean
- lint — clean
- Unit tests — 290/290 passed
- Integration tests — 23/23 passed
- Concurrent race test — 1 remaining message, 10 parallel requests, only 1 succeeds (validated)

**Known Limitations / Follow-ups:**
- H1 quota race: reserve-then-release not implemented; free path can over-grant on concurrent, addon path can over-grant by 1 before lock
- H6 UTC date reset for Asia/Bangkok (+7) accepted per spec; UI tooltip deferred to Phase 07/08
- H7 tier Literal case-sensitivity documented; no active bug
- M4 no purchase-race test (two parallel /purchase for same package)
- SQLite race test only; Postgres validation deferred to CI
- UpsellModal close doesn't refresh ChatLayout quota badge until next message interaction (minor UX gap)

## Success Criteria
- Free user can send 3 msgs/day, 4th blocked with 402.
- After purchase + payment approval, addon balance reflects message_count.
- Pro tier answers visibly more detailed than Flash (manual eval 10 questions).
- Concurrent decrement test: no over-spending.
- Existing PDF package flow unaffected (regression test).

## Risk Assessment

| Risk | Mitigation |
|------|------------|
| Race condition in addon decrement | SELECT FOR UPDATE inside transaction |
| Payment webhook fires twice | Existing idempotency in fulfillment_service |
| User charged but addon not granted | Manual reconciliation tool in admin (Phase 07) |
| Expired addons miscounted | Query filters `expires_at > NOW() AND remaining_messages > 0` |
| Free counter reset issue across timezones | Use server UTC date consistently |
| Pro tier costs spike with abuse | Phase 06 rate limit caps Pro msgs per minute |

## Security Considerations
- `purchase` endpoint validates package is active + kind=chat_addon.
- `fulfill` cross-checks `payment.user_id == purchase.user_id`.
- Admin-only endpoints for package CRUD.
- Audit log: every addon decrement logs (user_id, msg_id, addon_id) for billing disputes.

## Next Steps / Dependencies
- **Unlocks:** Real revenue flow, supports Phase 06 rate limit (paid tier higher cap).
- **Required for:** Phase 08 cost monitoring (tier-segmented).
- **Parallel-safe with:** Phase 06 (different concerns).
