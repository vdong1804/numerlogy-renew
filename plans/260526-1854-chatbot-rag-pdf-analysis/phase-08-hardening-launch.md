# Phase 08 — Hardening: Cost Monitoring + Abuse Detection + Launch

## Context Links
- Depends on: All P1-P7
- Brainstorm: §5 risks, §6 success metrics

## Overview
- **Priority:** Critical (gate before public launch)
- **Status:** complete (code) / pending (operations)
- **Duration:** 1 week (2026-05-21 to 2026-05-28)
- **Description:** Cost dashboard with alerts, abuse detection (CAPTCHA after N failures, suspicious patterns), DSAR/GDPR data deletion, performance tuning, A/B test prompts, public launch readiness checklist.

## Key Insights
- Daily cost ceiling alert at $20 (≈$600/month) → page on-call.
- Abuse signals: rapid quota cycling across accounts, prompt injection patterns, identical query bursts from different IPs.
- DSAR: user can request deletion of all their chat data via `/api/profile/delete-chat-data`.
- A/B test prompts: feature flag table; randomly assign 10% of users to variant; measure citation accuracy + user retention.

## Requirements

### Functional
- Daily cost aggregation job → `chat_daily_metrics` table.
- Alert via email + Slack webhook when daily cost > threshold.
- Abuse detection job: flag users matching suspicious patterns, increment `abuse_score`.
- CAPTCHA (hCaptcha or Turnstile — Turnstile already in stack per `turnstile_service.py`) after 3 rate-limit hits.
- DSAR endpoint deletes user's conversations, messages, user_pdf_index, addon_purchases (with billing copy retained).
- Public launch checklist completed: monitoring, runbook, error budget, rollback plan.

### Non-Functional
- Cost dashboard refresh ≤5 min lag.
- Abuse flag fires within 10 min of pattern detection.
- Rollback to disable chatbot via feature flag in <1 min.

## Architecture

```
app/
├── jobs/
│   ├── aggregate_chat_metrics.py    # nightly + hourly cost rollup
│   └── detect_chat_abuse.py         # pattern scan
├── services/chat/
│   ├── cost_monitor_service.py
│   ├── abuse_detection_service.py
│   └── ab_test_service.py
├── routers/profile.py               # +DELETE chat data
├── routers/admin/chatbot.py         # +cost alerts UI
alembic/versions/
└── 0015_hardening.py
docs/
├── chatbot-runbook.md
├── chatbot-launch-checklist.md
└── chatbot-cost-monitoring.md
```

## SQL Schema (alembic 0015)

```sql
CREATE TABLE chat_daily_metrics (
  date DATE PRIMARY KEY,
  msg_count_free INT NOT NULL DEFAULT 0,
  msg_count_paid INT NOT NULL DEFAULT 0,
  cache_hits INT NOT NULL DEFAULT 0,
  input_tokens_total BIGINT NOT NULL DEFAULT 0,
  output_tokens_total BIGINT NOT NULL DEFAULT 0,
  cost_usd NUMERIC(10,4) NOT NULL DEFAULT 0,
  rate_limit_hits INT NOT NULL DEFAULT 0,
  new_addon_purchases INT NOT NULL DEFAULT 0,
  unique_users INT NOT NULL DEFAULT 0
);

CREATE TABLE chat_abuse_flags (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
  ip VARCHAR(45),
  pattern VARCHAR(100) NOT NULL,    -- 'rapid_quota_cycle' | 'prompt_injection' | 'identical_burst'
  score INT NOT NULL DEFAULT 1,
  details JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  resolved_at TIMESTAMPTZ,
  resolution VARCHAR(50)             -- 'banned' | 'captcha_required' | 'cleared'
);
CREATE INDEX chat_abuse_user_idx ON chat_abuse_flags(user_id, created_at);

ALTER TABLE users ADD COLUMN chat_abuse_score INT NOT NULL DEFAULT 0;
ALTER TABLE users ADD COLUMN chat_captcha_required BOOLEAN NOT NULL DEFAULT FALSE;

CREATE TABLE chat_ab_test_assignments (
  user_id BIGINT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
  variant VARCHAR(50) NOT NULL,      -- 'control' | 'variant_a' | 'variant_b'
  assigned_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE chat_feature_flags (
  flag_key VARCHAR(100) PRIMARY KEY,
  enabled BOOLEAN NOT NULL DEFAULT FALSE,
  rollout_percent INT NOT NULL DEFAULT 0,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
INSERT INTO chat_feature_flags (flag_key, enabled, rollout_percent) VALUES ('chatbot_public', false, 0);
```

## Related Code Files

### Create
- `app/jobs/aggregate_chat_metrics.py` (≤150 LOC)
- `app/jobs/detect_chat_abuse.py` (≤180 LOC)
- `app/services/chat/cost_monitor_service.py` (≤120 LOC)
- `app/services/chat/abuse_detection_service.py` (≤180 LOC)
- `app/services/chat/ab_test_service.py` (≤100 LOC)
- `app/services/chat/feature_flag_service.py` (≤80 LOC)
- `alembic/versions/0015_hardening.py`
- `docs/chatbot-runbook.md`
- `docs/chatbot-launch-checklist.md`
- `docs/chatbot-cost-monitoring.md`
- `tests/services/chat/test_cost_monitor_service.py`
- `tests/services/chat/test_abuse_detection_service.py`
- `tests/jobs/test_aggregate_chat_metrics.py`

### Modify
- `app/routers/profile.py` — add `DELETE /chat-data` endpoint
- `app/routers/chat/messages.py` — feature flag check + abuse score gate + CAPTCHA check
- `app/services/chat/prompt_builder.py` — A/B variant prompt selection
- `app/services/turnstile_service.py` — extend for chat CAPTCHA
- `app/main.py` — register hourly + daily jobs

## Cost Calculation

```python
# Gemini pricing (as of 2026, update yearly):
PRICING = {
    "gemini-2.0-flash":   {"input": 0.10 / 1e6, "output": 0.40 / 1e6, "cached_input": 0.025 / 1e6},
    "gemini-2.5-pro":     {"input": 1.25 / 1e6, "output": 5.00 / 1e6, "cached_input": 0.31 / 1e6},
    "text-embedding-004": {"input": 0.025 / 1e6, "output": 0},
}

def calc_msg_cost(model, input_tokens, output_tokens, cached_tokens=0):
    p = PRICING[model]
    return (
        (input_tokens - cached_tokens) * p["input"]
        + cached_tokens * p.get("cached_input", p["input"])
        + output_tokens * p["output"]
    )
```

## Abuse Patterns

| Pattern | Detection | Action |
|---------|-----------|--------|
| `rapid_quota_cycle` | Same IP creating multiple accounts hitting free limit within 1h | CAPTCHA + email verify required |
| `prompt_injection` | Message contains "ignore previous", "system:", role markers | Block message + +5 abuse score |
| `identical_burst` | Same content sent 10+ times in 1h across users/IPs | Block content fingerprint + flag |
| `quota_exhaustion_grief` | User exhausts quota daily without ever purchasing | Soft signal — analytics only |
| `pdf_upload_spam` | 20+ uploads in 1h from same user | Throttle uploads to 5/day |

## Implementation Steps

1. **Schema** — Alembic 0015 with all new tables.

2. **Cost monitor**
   ```python
   class CostMonitorService:
       async def record_message_cost(message_id, model, in_tokens, out_tokens, cached): ...
       async def get_today_cost() -> Decimal
       async def alert_if_exceeded(threshold_usd: Decimal):
           # email + Slack webhook
   ```

3. **Aggregate job**
   - Hourly: incremental update to `chat_daily_metrics` for today.
   - Nightly: finalize previous day + clean up.

4. **Abuse detection job**
   - Runs every 15 min.
   - Queries patterns above, inserts `chat_abuse_flags`, updates `users.chat_abuse_score`.
   - Score >10 → `chat_captcha_required = TRUE`.
   - Score >50 → suspend chat for user; notify admin.

5. **Prompt injection filter**
   - Inline check in messages router (cheap regex): block known patterns before LLM.
   - Patterns: `(?i)(ignore|disregard|forget) (previous|prior|above) (instructions|prompt)`, `(?i)system:`, `<\|.*\|>`, etc.

6. **CAPTCHA flow**
   - Frontend: if `user.chat_captcha_required` → show Turnstile widget; submit token with message.
   - Backend: verify token before processing. Clear flag after 5 successful CAPTCHA solves.

7. **DSAR endpoint**
   ```python
   @router.delete("/chat-data")
   async def delete_my_chat_data(user=Depends(get_current_user)):
       # delete conversations cascade
       # delete user_pdf_index cascade
       # anonymize chat_addon_purchases (set user_id NULL? — keep for billing)
       # log to audit_log
   ```

8. **A/B test**
   - On first chat: assign variant (deterministic hash of user_id).
   - `prompt_builder` loads variant-specific prompt from `chat_system_settings` keyed by variant.
   - Track outcomes via `chat_ab_test_assignments` join with metrics.

9. **Feature flag**
   - `chatbot_public` flag check in router; if disabled, return 503 with maintenance msg.
   - Rollout: start 5% → 25% → 50% → 100% over launch week.

10. **Launch checklist** (in `docs/chatbot-launch-checklist.md`):
    - [ ] Alembic 0010-0015 applied on prod
    - [ ] Gemini API key + budget configured in GCP
    - [ ] Cost alert webhooks tested
    - [ ] Abuse detection runs every 15 min
    - [ ] Backfill KB chunks complete
    - [ ] E2E test on prod (with test user)
    - [ ] Rate limit verified
    - [ ] Rollback procedure documented + drilled
    - [ ] On-call rotation set for first week
    - [ ] Sentry error monitoring includes chat namespace
    - [ ] DSAR endpoint tested
    - [ ] Privacy policy updated to mention chat data

11. **Runbook** (in `docs/chatbot-runbook.md`):
    - Common issues: Gemini API down → fallback msg; pgvector slow → ef_search; cost spike → tighten limits.
    - Escalation path.

12. **Post-launch monitoring** (first 30 days)
    - Daily check: cost vs budget, cache hit rate, abuse flags, conversion rate.
    - Weekly: prompt iteration based on user feedback + manual citation eval.

## Todo List

### Code Implementation (completed 2026-05-28)
- [x] Alembic 0015 migration
- [x] Implement `cost_monitor_service.py` with pricing table
- [x] Implement `aggregate_chat_metrics.py` job (hourly + nightly)
- [x] Implement `abuse_detection_service.py` (5 patterns)
- [x] Implement `detect_chat_abuse.py` job (15-min interval)
- [x] Implement prompt injection filter in messages router
- [x] Wire CAPTCHA gate (frontend + backend using Turnstile)
- [x] Implement `feature_flag_service.py` + chatbot_public flag check
- [x] Implement `ab_test_service.py` + variant routing in prompt_builder
- [x] Add DSAR `DELETE /api/profile/chat-data` endpoint
- [x] Write `docs/chatbot-runbook.md`
- [x] Write `docs/chatbot-launch-checklist.md`
- [x] Write `docs/chatbot-cost-monitoring.md`

### Production Operations (pending manual action)
- [ ] Set up Slack webhook + email alert pipeline for cost
- [ ] Run E2E load test (100 concurrent users for 30 min)
- [ ] Soft launch at 5% → ramp daily
- [ ] GCP budget alerts configured
- [ ] Update ToS to mention AI chat disclaimer
- [ ] On-call rotation established for launch week
- [ ] Manual E2E test on prod with test user
- [ ] Full launch + announcement
- [ ] First-month KPI review

### Docs (handled by docs-manager separately)
- [ ] Update `docs/project-overview-pdr.md` with chatbot feature
- [ ] Update `docs/development-roadmap.md` with chatbot milestone
- [ ] Update `docs/project-changelog.md` post-launch

## Success Criteria
- 30 days post-launch: cost <$500/month at 10k MAU.
- Hallucination rate <5% (manual eval 100 random samples).
- Free→Paid conversion >3%.
- Zero P0 incidents in first 30 days.
- Cache hit rate >25% sustained.
- DSAR endpoint successfully deletes test user's data (verify with audit).
- Feature flag rollback test: disable in admin → service returns 503 within 60s.

## Risk Assessment

| Risk | Mitigation |
|------|------------|
| Cost spike on launch day | Feature flag throttle to 5%; auto-disable if daily cost >$30 |
| Abuse during initial publicity | Aggressive rate limit week 1; require email verify for new accounts week 1 |
| Gemini API outage | Graceful degradation: queue messages, retry; show "AI service temporarily unavailable" |
| Migration failure on prod | Test all 6 migrations on staging first; have explicit downgrade scripts |
| Negative user feedback on quota | Free 5/day instead of 3 for first 2 weeks → tighten if cost OK |
| Legal: AI advice disclaimer | Add disclaimer in chat UI + ToS update before launch |

## Security Considerations
- DSAR: confirm deletion idempotent + auditable.
- Abuse flags reviewed by admin (false positives possible).
- CAPTCHA tokens have short TTL (validated server-side, not stored).
- Cost dashboard exposes financial data — admin-only.
- Feature flag changes audited.

## Next Steps / Post-launch
- Phase 09 (optional): Reranker (cross-encoder) for paid tier quality boost.
- Phase 10 (optional): Multimodal Gemini for image-based PDF.
- Phase 11 (optional): Voice input (Whisper + TTS).
- Continuous: prompt iteration, KB expansion, addon pricing optimization.

## Open Questions (deferred from brainstorm)
1. Conversation retention period (30/90/365 days?) — propose 365 for paid, 90 for free.
2. Final addon pricing (basic 49k / standard 119k / premium 349k VND) — needs business sign-off.
3. Multimodal fallback for image PDFs — measure pypdf failure rate first, decide in Phase 03 review.
4. Rerank for paid tier — defer to post-launch unless citation accuracy <80%.
5. EN locale support — keep VN-only at launch; revisit at 5k MAU.
