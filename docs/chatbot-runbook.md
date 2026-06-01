# Chatbot Runbook (Phase 08)

Operational guide for the Numerology RAG chatbot. Keep this open during on-call.

## Quick toggles

| Action | Command |
|---|---|
| Disable chatbot entirely | `UPDATE chat_feature_flags SET enabled=FALSE WHERE flag_key='chatbot_public';` |
| Reduce rollout to 5% | `UPDATE chat_feature_flags SET rollout_percent=5 WHERE flag_key='chatbot_public';` |
| Clear an admin prompt override | `DELETE FROM chat_system_settings WHERE key='chat_system_prompt';` |
| Reset a user's CAPTCHA gate | `UPDATE users SET chat_captcha_required=FALSE, chat_abuse_score=0 WHERE id=<id>;` |
| Unsuspend a user | `UPDATE users SET chat_suspended_at=NULL WHERE id=<id>;` |

Feature-flag cache is in-process (60s TTL). To force-refresh, restart workers or wait one minute.

## Common incidents

### 1. Daily cost spike

Symptom: cost alert email or Slack ping; `chat_daily_metrics.cost_usd > $20`.

1. Check `chat_daily_metrics` for today vs yesterday — which model dominates?
2. Inspect `chat_messages` for unusual user_ids:
   ```sql
   SELECT c.user_id, COUNT(*), SUM(m.input_tokens + m.output_tokens) AS toks
   FROM chat_messages m
   JOIN chat_conversations c ON c.id = m.conversation_id
   WHERE m.created_at > NOW() - INTERVAL '1 hour'
   GROUP BY c.user_id
   ORDER BY toks DESC LIMIT 10;
   ```
3. If a single user dominates: bump `chat_abuse_score` to suspend.
4. If broad spike: drop `rollout_percent` to 25% to shed load; investigate.
5. Hard kill if needed: set `chatbot_public.enabled=FALSE`.

### 2. DeepSeek API down

Symptom: 502 errors in chat endpoint; LLM timeouts in logs.

- Service degrades gracefully (returns `Vui lòng thử lại sau giây lát.`) — no kill needed.
- Check Sentry for `LlmError` rate.
- If sustained >5 min, flip `chatbot_public.enabled=FALSE` to stop the bleed.
- DeepSeek egress: `api.deepseek.com` (CN region) — confirm firewall rules before prod cutover.

### 3. pgvector slow / retrieval timeout

- Check `pg_stat_statements` for kb_chunks queries >1s.
- HNSW index `ef_search`: lower to 40 (default 100) for faster but slightly less accurate search.
- If retrieval consistently fails, the LLM falls back to the no-info message — UX degraded but safe.

### 4. Abuse pattern fires

- Check `chat_abuse_flags` ordered by `created_at DESC LIMIT 50`.
- For `identical_burst`: spam attack. Block content via WAF if persistent.
- For `pdf_upload_spam`: tighten `chat_addon` upload limit.
- For `prompt_injection`: review samples in `details->>'sample'`; refine regex if false-positive rate >5%.

### 5. DSAR request

- User hits `DELETE /api/profile/chat-data`.
- Verify in audit log (server log line `DSAR delete chat-data user=...`).
- Confirm rowcounts returned in response.
- Addon purchases are anonymized (user_id NULL) — billing trail preserved.

## Rollback

1. Set `chatbot_public.enabled=FALSE` (1 SQL statement, propagates in <60s).
2. If migration 0015 needs reversal: `alembic downgrade 0014`. **Warning:** this drops Phase 8 tables; user abuse state is lost.
3. Backups: daily Postgres dump (see `deploy/backup.sh`) retains 14 days.

## Escalation

| Symptom | Owner | Page? |
|---|---|---|
| Cost >$30 / 1h | DongVD | Yes |
| Sustained 5xx >2% / 5min | DongVD | Yes |
| Abuse flag bulk-fires >100 in 15min | DongVD | Yes |
| Single-user complaint | Support queue | No |

## Health checks

- `/health` → 200 = API alive (does not exercise LLM).
- Scheduler jobs: see `app.jobs.scheduler.setup_jobs` logs at boot.
- Cost rollup freshness: `SELECT MAX(updated_at) FROM chat_daily_metrics;` should be <2h old.
