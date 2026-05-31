# Chatbot Launch Checklist (Phase 08)

Walk this list before flipping `chatbot_public.enabled=TRUE` for the public.

## Infrastructure

- [ ] All migrations `0010` → `0015` applied on production DB.
- [ ] `CREATE EXTENSION vector;` confirmed on production Postgres 16.
- [ ] Gemini API key (`GEMINI_API_KEY`) set in production env; quota verified in GCP console.
- [ ] Daily Gemini budget alert configured at $25 (warning) and $50 (critical) in GCP Billing.
- [ ] Slack webhook URL stored in env (`CHAT_COST_ALERT_SLACK_WEBHOOK`).
- [ ] Admin email for cost alerts (`CHAT_COST_ALERT_EMAIL`).
- [ ] Turnstile site + secret keys set; tested against a known-bad token in staging.
- [ ] Sentry DSN configured; chat namespace tagged.

## Data + content

- [ ] Knowledge-base ingestion complete; `kb_chunks` rowcount within expected range.
- [ ] System prompt reviewed by content owner; admin override slot empty (uses in-code constant).
- [ ] At least 1 admin user exists for `/admin/chatbot`.

## Code paths

- [ ] DSAR endpoint `DELETE /api/profile/chat-data` returns 200 on a test account.
- [ ] CAPTCHA flow: artificially set `chat_captcha_required=TRUE` on a test account; verify 401 without token, 200 with valid Turnstile token.
- [ ] Prompt injection regex blocks "ignore previous instructions" sample → 400.
- [ ] Feature flag toggle: set `chatbot_public.enabled=FALSE`; verify 503 within 60s; re-enable.
- [ ] Rate-limit hit increments `chat_daily_metrics.rate_limit_hits`.

## Operations

- [ ] APScheduler running in production; verify jobs registered via boot logs:
  - [ ] `aggregate_chat_metrics_hourly`
  - [ ] `aggregate_chat_metrics_nightly`
  - [ ] `detect_chat_abuse`
- [ ] Run `python -m app.jobs.aggregate_chat_metrics --nightly` manually once; row appears in `chat_daily_metrics`.
- [ ] Run `python -m app.jobs.detect_chat_abuse` manually; completes without error.
- [ ] Test cost alert path: temporarily set threshold to $0.01 with prod data → alert email + Slack arrive.

## Observability

- [ ] Sentry receives `LlmError` events on simulated Gemini outage.
- [ ] Cost dashboard accessible at `/admin/chatbot/cost` (admin only).
- [ ] Runbook (`docs/chatbot-runbook.md`) reviewed by on-call.
- [ ] Cost monitoring doc (`docs/chatbot-cost-monitoring.md`) reviewed by finance owner.

## Legal

- [ ] Privacy policy mentions chat data retention (90d free / 365d paid).
- [ ] ToS update lists AI assistant + numerology-not-medical-advice disclaimer.
- [ ] DSAR procedure documented for support.

## Rollout plan

| Day | rollout_percent | Trigger to advance |
|---|---|---|
| 0 | 5 | Cost <$5; zero P0 errors; cache hit rate >15% in 24h |
| 1 | 25 | Same gates; abuse flags <10 |
| 3 | 50 | Same gates; conversion >2% |
| 7 | 100 | Same gates; finance sign-off on weekly run-rate |

Rollback at any stage: flip `chatbot_public.enabled=FALSE` (1 SQL, <60s propagation).

## Post-launch (week 1)

- [ ] Daily KPI review: cost vs budget, cache hit rate, abuse count, conversion.
- [ ] Daily manual eval of 20 chat samples for citation accuracy.
- [ ] Tighten prompt injection regex if FP rate >5%.
- [ ] First weekly retro: prompt tuning candidates from user feedback.

## Sign-off

| Role | Name | Date |
|---|---|---|
| Tech lead | DongVD | _____ |
| Product | _____ | _____ |
| Finance | _____ | _____ |
