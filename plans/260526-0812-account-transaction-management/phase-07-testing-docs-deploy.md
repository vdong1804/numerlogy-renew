# Phase 07 — Testing + Docs + Deploy

## Context Links
- [Plan overview](./plan.md)
- All prior phases

## Overview
- **Priority:** P0 (go-live readiness)
- **Status:** pending
- **Duration:** Tuần 8 (5 ngày dev)
- **Description:** Test coverage ≥80%, E2E flows (Cypress), load test webhook (k6), update docs, zero-downtime deploy production với migration mới + env vars mới + scheduler container.

## Key Insights
- Cypress đã có sẵn trong Numerology-Landing-Page → reuse pattern
- pytest-asyncio đã setup → tests existing pattern
- Deploy hiện tại: docker-compose.prod.yml + deploy.sh; cần update để cover scheduler + email worker (nếu separate)
- Migration 0004-0007 phải zero-downtime: backward-compatible (không drop column trước khi remove code reference)

## Requirements

### Functional
- Unit tests ≥80% coverage cho: order_service, sepay_service, fulfillment_service, email_service, email_dispatcher, all jobs
- Integration tests: order create + webhook + fulfillment end-to-end (testcontainers postgres)
- E2E Cypress: 3 flows critical:
  1. User register → nhận lead magnet PDF
  2. User mua gói qua /shop → check-out → mock webhook → quota tăng → my-account hiện gói
  3. User mua báo cáo lẻ → mock webhook → my-account/reports hiện PDF download được
- Load test k6: 100 concurrent webhook events trong 1 phút, verify no double fulfill, P99 <500ms
- Smoke test post-deploy: register + login + create order + manual mark-paid + my-account works

### Non-functional
- Deploy với migration không gây downtime API
- Rollback plan rõ ràng <10 phút
- Backup verify restore-able

## Architecture

### Test layers

```
tests/
├── unit/          (existing, expand)
│   ├── test_order_service.py
│   ├── test_sepay_service.py
│   ├── test_fulfillment_service.py
│   ├── test_email_service.py
│   ├── test_email_dispatcher.py
│   ├── test_ref_code.py
│   └── test_jobs/*
│
├── integration/   (NEW with testcontainers)
│   ├── conftest.py            # testcontainers postgres fixture
│   ├── test_order_flow.py     # create → fulfill end-to-end
│   ├── test_sepay_webhook_flow.py
│   └── test_my_account_flow.py
│
└── load/          (NEW)
    └── k6/
        ├── webhook-load.js
        └── shop-browse-load.js

Numerology-Landing-Page/cypress/
├── e2e/
│   ├── shop-purchase-package.cy.ts    # NEW
│   ├── shop-purchase-report.cy.ts     # NEW
│   ├── register-leadmagnet.cy.ts      # NEW
│   └── my-account-navigation.cy.ts    # NEW
└── support/
    └── commands.ts                    # MODIFY: add mockSePayWebhook helper
```

### Deploy strategy (zero-downtime)

1. **Pre-deploy:**
   - Backup DB (deploy/backup.sh)
   - Verify staging env passes all tests
   - DNS Resend verified (Phase 5 prerequisite)
2. **Deploy steps:**
   - SSH server, pull latest code
   - `docker compose -f docker-compose.prod.yml build api`
   - Run migration: `docker compose run --rm api alembic upgrade head` (additive only)
   - Seed: `docker compose run --rm api python scripts/seed_products.py`
   - `docker compose up -d api email-worker` (rolling restart, blue-green if possible)
   - `docker compose restart nginx` (graceful)
3. **Post-deploy verify:**
   - Smoke test script
   - Sentry no new errors trong 15 phút
   - Webhook test transaction nhỏ (vd 1000đ)
4. **Rollback (<10min):**
   - `git checkout <previous-tag>`
   - `docker compose up -d --build api email-worker`
   - Migration rollback: chỉ rollback nếu cần (additive migrations safe to keep)

## Related Code Files

### Create
- `numerology-api/tests/integration/conftest.py`
- `numerology-api/tests/integration/test_order_flow.py`
- `numerology-api/tests/integration/test_sepay_webhook_flow.py`
- `numerology-api/tests/integration/test_my_account_flow.py`
- `numerology-api/tests/load/k6/webhook-load.js`
- `numerology-api/tests/load/k6/shop-browse-load.js`
- `Numerology-Landing-Page/cypress/e2e/shop-purchase-package.cy.ts`
- `Numerology-Landing-Page/cypress/e2e/shop-purchase-report.cy.ts`
- `Numerology-Landing-Page/cypress/e2e/register-leadmagnet.cy.ts`
- `Numerology-Landing-Page/cypress/e2e/my-account-navigation.cy.ts`
- `numerology-api/scripts/smoke_test_post_deploy.sh`
- `numerology-api/deploy/MIGRATION-0004-0007-RUNBOOK.md`
- `numerology-api/deploy/ROLLBACK-PHASE-7.md`
- `docs/sepay-integration-runbook.md`
- `docs/email-setup-runbook.md` (Phase 5 đã có, verify đầy đủ)
- `docs/operations-runbook.md` (Phase 6 đã có, verify đầy đủ)

### Modify
- `numerology-api/pyproject.toml` — add `testcontainers[postgres]`, `pytest-cov`
- `numerology-api/tests/conftest.py` — share fixtures với integration
- `numerology-api/deploy/docker-compose.prod.yml` — add `email-worker` service nếu separate (hoặc keep APScheduler in-process)
- `numerology-api/deploy/deploy.sh` — add seed step, smoke test
- `numerology-api/deploy/env.prod.example` — full env vars from Phase 2/5/6
- `numerology-api/deploy/nginx.conf` — rate limit cho /webhooks/sepay endpoint (defense in depth)
- `Numerology-Landing-Page/cypress.config.js` — add baseUrl test env, verify config
- `docs/codebase-summary.md` — update với new tables, endpoints, components
- `docs/system-architecture.md` — diagram updated (order flow, webhook, email)
- `docs/development-roadmap.md` — mark phase complete
- `docs/project-changelog.md` — entry version 1.1 release notes

## Implementation Steps

1. **Coverage audit** — run `pytest --cov=app --cov-report=term-missing`, identify gaps
2. **Unit test gaps** — fill cho mỗi service/job đạt ≥80%
3. **Integration testcontainers setup** — `conftest.py` spin postgres container per session, run migrations
4. **Integration test order flow** — create user → POST /orders → POST mock webhook → assert order paid + user_packages updated
5. **Integration test webhook flow** — verify idempotency (call webhook 2x), unmatched ref handling, amount mismatch
6. **Integration test my-account** — auth + endpoints return correct user-scoped data
7. **k6 webhook load test** — 100 concurrent unique webhooks → assert all fulfilled, no double, P99 latency
8. **Cypress E2E setup** — chuẩn bị test data fixtures, custom command `mockSePayWebhook`
9. **Cypress test register + lead magnet** — register → check email outbox count (test endpoint) → check user_reports count
10. **Cypress test purchase package** — login → /shop → click gói → /check-out → mock webhook → redirect /my-account → verify quota
11. **Cypress test purchase report** — similar, verify report PDF download
12. **Cypress my-account navigation** — flow qua 6 tabs, assert content
13. **Smoke test script** — bash script chạy 8-10 curl commands sau deploy
14. **Migration runbook** — document Alembic 0004-0007 trong order, rollback steps mỗi migration
15. **Rollback runbook** — Phase 7 specific (git tag, docker image, DB restore nếu cần)
16. **Runbooks SePay, Email, Ops** — verify đầy đủ từ Phase 2/5/6
17. **Update codebase-summary.md, system-architecture.md, changelog**
18. **Pre-deploy: staging full run** — deploy lên staging server, chạy full test suite + Cypress + k6
19. **Deploy production** — follow deploy steps strictly, không skip
20. **Post-deploy 24h monitoring** — Sentry, Resend dashboard, webhook success rate, manual spot check 5 users

## Todo List

- [ ] M1. Coverage audit current state
- [ ] M2. Fill unit test gaps (achieve ≥80%)
- [ ] M3. Integration tests setup testcontainers
- [ ] M4. Integration test order flow E2E
- [ ] M5. Integration test webhook idempotency + edge cases
- [ ] M6. Integration test my-account ownership
- [ ] M7. k6 webhook load test
- [ ] M8. Cypress E2E 4 tests
- [ ] M9. Smoke test script post-deploy
- [ ] M10. Migration runbook 0004-0007
- [ ] M11. Rollback runbook Phase 7
- [ ] M12. Verify runbooks SePay/Email/Ops complete
- [ ] M13. Update docs/codebase-summary, system-architecture, changelog
- [ ] M14. Staging full deploy + test pass
- [ ] M15. Production deploy
- [ ] M16. 24h post-deploy monitoring + spot check

## Success Criteria

- `pytest --cov` shows ≥80% overall, ≥85% cho services critical (order, sepay, fulfillment)
- Integration tests pass với testcontainers postgres clean
- k6 load: 100 concurrent webhooks, 0 errors, 0 double-fulfill, P99 <500ms
- Cypress 4 E2E pass headless trong CI
- Smoke test post-deploy: 10/10 commands return 200
- Staging deployed + tested full flow trước production
- Production deploy <30 phút downtime (target <5 phút với rolling)
- 24h monitoring: 0 critical Sentry errors, email deliverability ≥95%, webhook success ≥99%
- DB backup verified restorable trên separate machine

## Risk Assessment

| Risk | Mức | Mitigation |
|------|-----|-----------|
| Migration 0004-0007 lỗi trên prod data | Cao | Test trên staging với prod backup copy; additive only (no destructive drops); rollback runbook tested |
| Deploy gây downtime > 5 phút | Cao | Blue-green hoặc rolling với nginx upstream switching; pre-warm cache; nếu single instance, accept 1-2 phút |
| Cypress flaky tests | TB | Use cy.intercept() cho stable mocks; retry config 2; tag flaky as quarantine |
| k6 load test trên prod gây downtime | Cao | Chạy chỉ trên staging, KHÔNG prod; nếu cần prod test, schedule off-peak |
| Lỗi production phát hiện sau go-live | Cao | Phased rollout: 24h monitoring intense, sẵn sàng rollback; alerting Sentry + uptime monitor |
| Email deliverability rate thấp post-go-live | TB | Warm-up 1 tuần trước go-live (gửi internal tests); fallback SMTP nếu Resend issue |
| User experience confusing flow mới | TB | Soft launch với banner "Tính năng mới", tutorial popup; hỗ trợ live chat 48h đầu |

## Security Considerations

- Pre-deploy: rotate JWT_SECRET, EMAIL_SECRET, SEPAY_API_KEY nếu shared dev
- Verify CORS origins chỉ allow prod domain
- Disable DEBUG, set ENVIRONMENT=production
- Verify HTTPS redirect (nginx force 301)
- Database password strong, không log
- Backup file encrypted (gpg) trước upload offsite
- Sentry: confirm filter PII active
- Webhook IP whitelist active prod

## Deploy Checklist (final)

```
PRE-DEPLOY
□ All tests pass (unit + integration + e2e)
□ k6 load test pass on staging
□ Backup DB current state
□ Staging tested 24h, no critical issues
□ DNS Resend verified
□ SePay sandbox tested, webhook URL configured
□ Env vars prod set (SEPAY_API_KEY, RESEND_API_KEY, SENTRY_DSN, EMAIL_SECRET, etc.)
□ Communication: tell users about maintenance window (if any)

DEPLOY
□ SSH server, git pull, checkout tag
□ docker compose build api
□ alembic upgrade head (verify success)
□ python scripts/seed_products.py (verify idempotent)
□ docker compose up -d api email-worker
□ docker compose restart nginx
□ Smoke test script pass

POST-DEPLOY
□ Sentry no new critical errors (15 phút monitoring)
□ Test live: register user, mua gói nhỏ thật, check fulfill
□ Resend dashboard shows emails sent
□ Webhook events log shows valid traffic
□ Update changelog version 1.1 released
□ Document any hotfixes needed
```

## Next Steps (Phase 2 / Future)
- Refund workflow + audit log
- Multi-currency (Stripe cho user quốc tế)
- Subscription auto-renew (cần cổng support recurring)
- Coupon/voucher/referral
- Zalo ZNS notification
- Admin audit log table
- Analytics dashboard nâng cao (cohort, funnel)
- Mobile app (React Native)
