# Phase 03 — Tests, Code Review, Docs

## Overview
- **Priority:** Medium
- **Status:** pending
- **Depends on:** Phase 01, 02

## Steps

1. **Backend tests** (`numerology-api/tests/integration/test_health_and_auth.py`)
   - Drop `TestAuthSocial*` (none currently)
   - Add `TestForgotPassword`: returns 202 for unknown email, returns 202 for known email
   - Add `TestResetPassword`: happy path, invalid token, expired token, reused token

2. **Run pytest** via tester subagent

3. **Frontend type check**
   - `npm run check-types` in `Numerology-Landing-Page`

4. **Code review subagent** — full diff review

5. **Docs sync** (`docs-manager` subagent)
   - `docs/project-overview-pdr.md` — auth section: remove OAuth bullet, add forgot/reset
   - `docs/system-architecture.md` — remove SNS / OAuth flow, table `social_accounts` → drop; add `password_reset_tokens`
   - `docs/project-changelog.md` — entry for SNS removal + new auth pages

## Success Criteria
- All pytest pass
- TypeScript compiles
- Code review score ≥ 9.5 (or user approval)
- Docs updated
