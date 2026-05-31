# Chatbot Cost Monitoring (Phase 08)

How daily cost is computed, alerted on, and read back from the dashboard.

## Pricing table (USD per 1M tokens, as of 2026)

| Model | Input | Output | Cached input |
|---|---|---|---|
| `gemini-2.0-flash` | $0.10 | $0.40 | $0.025 |
| `gemini-2.5-pro` | $1.25 | $5.00 | $0.31 |
| `text-embedding-004` | $0.025 | n/a | n/a |

Source of truth: `app/services/chat/cost_monitor_service.py::PRICING`. Update yearly when Gemini revises rates and bump revision date in this doc.

## Cost formula

```
cost_per_message = ((input_tokens - cached_tokens) × input_rate)
                 + (cached_tokens × cached_input_rate)
                 + (output_tokens × output_rate)
```

Cache hits (semantic cache, no LLM call) cost $0 and bump `cache_hits`, not `cost_usd`.

## Data flow

1. **Hot path** — every assistant message hits `CostMonitorService.record_message_cost()`. Upsert into `chat_daily_metrics` for today (UPSERT on `date` PK).
2. **Hourly job** — `app.jobs.aggregate_chat_metrics.run_hourly` recomputes today's row from `chat_messages` (truth) and checks the alert threshold.
3. **Nightly job** — `run_nightly` at 03:30 UTC finalizes the previous day's row; also recomputes `unique_users` and `new_addon_purchases`.

## Schema (`chat_daily_metrics`)

| Column | Meaning |
|---|---|
| `date` | UTC date, PK |
| `msg_count_free` | Free-tier assistant messages |
| `msg_count_paid` | Paid-tier (pro/addon) assistant messages |
| `cache_hits` | Semantic cache hits (no LLM billed) |
| `input_tokens_total` | All input tokens billed today |
| `output_tokens_total` | All output tokens billed today |
| `cost_usd` | NUMERIC(10,4) — running sum |
| `rate_limit_hits` | 429 responses today |
| `new_addon_purchases` | Add-on purchases completed today |
| `unique_users` | DISTINCT user_ids who sent ≥1 message today |
| `updated_at` | Last hot-path or job touch |

## Alerts

`CostMonitorService.alert_if_exceeded()` fires when `today.cost_usd > threshold` (default $20).

| Channel | Trigger | Env var |
|---|---|---|
| Email | Daily cost > $20 | `CHAT_COST_ALERT_EMAIL` |
| Slack webhook | Daily cost > $20 | `CHAT_COST_ALERT_SLACK_WEBHOOK` |

Alert is checked once per hourly tick — duplicates are possible (1×/hour after first breach). To silence, raise the threshold via env or rotate the day.

## Dashboard

- Admin route: `/admin/chatbot/cost` (admin-only).
- Refresh lag: ≤5 min (hourly job + hot-path UPSERT).
- Recommended views:
  - Daily $ for last 30 days.
  - Cost / unique user (today).
  - Free vs paid message split.
  - Cache hit rate.

## Tuning levers if cost spikes

1. **Free quota** — drop from 3 → 2 (`settings.chat_free_daily_limit`).
2. **Cache TTL** — raise `semantic_cache_ttl_hours` from 24 → 72 (more reuse, slightly stale answers).
3. **Cache threshold** — relax `semantic_cache_threshold` 0.92 → 0.88 to capture more near-misses.
4. **Pro top_k** — drop `rag_top_k_paid` 8 → 6 (less context = fewer input tokens).
5. **Suspend new account creation** — manual; via admin toggle.
6. **Kill switch** — `chatbot_public.enabled=FALSE` (last resort).

## Budget math

Target: <$500/month at 10k MAU. With ~3 free msgs/day cap + 25% cache hit rate + ~600 tok avg per Flash call:

```
flash_msg_cost ≈ 600 × $0.10/1M + 400 × $0.40/1M ≈ $0.00022
3 msgs × 30 days × 0.75 (cache miss) × $0.00022 ≈ $0.015/user/month
$0.015 × 10k MAU ≈ $150/month for free tier alone.
```

Pro tier adds ~$0.005/message; capped by quota addons. Conservatively budget $500/month covers free + ~15% conversion to paid.

## When pricing changes

1. Update `PRICING` dict in `cost_monitor_service.py`.
2. Update the table at the top of this doc.
3. Backfill is OPTIONAL — historical `cost_usd` rows stay at old rates; only forward computations use new rates.
