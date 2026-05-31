# Docs Update Report: Phase 05 (Chat Quota + Add-on Packages)

**Date:** 2026-05-28  
**Phase:** Phase 05 Chatbot RAG — Chat Quota + Add-on Packages  
**Status:** Complete

---

## Files Updated

### 1. system-architecture.md
**Section Added:** 2e. Chat Quota + Add-on Packages (Chatbot RAG — Phase 05)  
**Delta:** +147 LOC (quota resolution flow, services, endpoints, known issues, config)  
**Final LOC:** 735 (under 800 limit)  
**Summary:** Documented QuotaService, QuotaDecision, addon_fulfillment, new tables (chat_addon_purchases, packages columns), SePay webhook branching (NSQ vs CHATADDON), SSE quota_exceeded events, 3 known issues deferred to Phase 06.

### 2. codebase-summary.md
**Section Updated:** Chat Module (Phase 04 + Phase 05) + file list  
**Delta:** +12 LOC (Phase 05 files + highlights)  
**Final LOC:** 464 (well under limit)  
**Summary:** Added use-quota hook, QuotaBadge/UpsellModal components, upgrade page + AddonList/AddonCard, Phase 05 highlights in header.

### 3. code-standards.md
**Section Added:** Idempotent Payment Fulfillment (Phase 05+)  
**Delta:** +32 LOC (pattern + example code)  
**Final LOC:** 615 (under limit)  
**Summary:** Documented payment idempotency via unique payment_id key, check-before-insert flow, webhook retry safety.

### 4. deployment-guide.md
**Section Modified:** Database Migrations (Local Development)  
**Delta:** +10 LOC (migration 0012 note)  
**Final LOC:** 797 (under 800 limit)  
**Summary:** Added note on alembic 0012: chat_addon_purchases table + packages columns, partial index, deploy action (upgrade head).

### 5. project-changelog.md
**Section Added:** [2026-05-28] — Chat Quota + Add-on Packages Phase 05  
**Delta:** +40 LOC (backend + frontend summary, known issues, report links)  
**Final LOC:** 669 (under limit)  
**Summary:** Captured Phase 05 scope: QuotaService, addon_fulfillment, new routers/models, migration 0012, SePay webhook, frontend components/hooks, admin package form, test results (290/0 pass/fail), 3 deferred issues.

### 6. development-roadmap.md
**Section Added:** Chatbot RAG Phase 05 — Chat Quota + Add-on Packages (Monetization)  
**Delta:** +25 LOC (status complete, deliverables, known issues, next steps)  
**Final LOC:** 557 (under limit)  
**Summary:** Marked Phase 05 complete; documented backend services, routers, models, migration, frontend components, known issues (C1 webhook path, C2 decrement race, H3 polling), Phase 06 preview.

### 7. project-overview-pdr.md
**Section Modified:** Content & Utilities (Phase 05 — Done)  
**Delta:** +1 LOC (package types clarification)  
**Final LOC:** 141 (minimal)  
**Summary:** Clarified package management includes both PDF downloads + Chat AI add-ons with 30d validity.

---

## Files NOT Updated

- **docs/design-guidelines.md** — no design changes in Phase 05
- **docs/analytics-events.md** — no new events; quota queries not user-facing events
- **docs/legal-content-sources.md** — no legal impact
- **docs/runbook-payment-incident.md** — no new incident patterns (see Phase 06 for webhook fixes)
- **docs/go-live-runbook.md** — no deployment changes (migration included in standard upgrade flow)
- **docs/post-launch-monitoring.md** — no new monitoring metrics (existing quota alerts cover addon depletion)
- **docs/lint-cleanup-backlog.md** — not touched

---

## Metrics

| File | Before | After | Delta | Status |
|------|--------|-------|-------|--------|
| system-architecture.md | 588 | 735 | +147 | ✅ |
| codebase-summary.md | 452 | 464 | +12 | ✅ |
| code-standards.md | 583 | 615 | +32 | ✅ |
| deployment-guide.md | 787 | 797 | +10 | ✅ |
| project-changelog.md | 629 | 669 | +40 | ✅ |
| development-roadmap.md | 532 | 557 | +25 | ✅ |
| project-overview-pdr.md | 140 | 141 | +1 | ✅ |
| **Total** | **3711** | **3978** | **+267** | **✅ All under 800 LOC** |

---

## Key Coverage Points

### Phase 05 Implementation Details Documented
- ✅ QuotaService (check/decrement, atomic SELECT FOR UPDATE on addon, ON CONFLICT on free)
- ✅ addon_fulfillment.fulfill_chat_addon (idempotent via payment_id UNIQUE)
- ✅ Three endpoints: GET /api/chat/addons, POST .../purchase, GET /api/chat/quota
- ✅ Migration 0012 schema changes (chat_addon_purchases table, packages columns)
- ✅ SePay webhook extended matcher (NSQ vs CHATADDON{id} prefix)
- ✅ Quota resolution priority: addon > free > 402
- ✅ Frontend components: QuotaBadge, UpsellModal, upgrade page, use-quota hook
- ✅ Admin form enhancements: package_kind selector, conditional ChatAddonFields
- ✅ Test coverage: 290 pass, 0 fail, tsc/lint clean

### Known Issues Clearly Flagged
- **C1:** SePay webhook path unreachable (UserPayment created, but webhook doesn't trigger fulfillment) → Phase 06 fix
- **C2:** Stream decrement race (post-commit window, client disconnect) → Phase 06 fix
- **H3:** No polling on /chat/upgrade (manual navigation required) → Phase 06 fix

### Backend Architecture Updated
- Added section 2e (Chat Quota + Add-ons) to system-architecture.md detailing tables, services, resolution flow, config

### Code Standards Enhanced
- New idempotent fulfillment pattern documented with example

---

## Validation

✅ All files under 800 LOC limit  
✅ No broken links (internal references verified)  
✅ Consistent terminology (QuotaService, addon_fulfillment, chat_addon_purchases)  
✅ Code examples match actual implementation (from Phase 05 reports)  
✅ Cross-references to Phase 06 deferred work noted  
✅ Vietnamese labels preserved (e.g., "Hết lượt", UpsellModal Vietnamese UI)

---

## Unresolved Questions

None. All Phase 05 deliverables captured. Phase 06 follow-ups documented.
