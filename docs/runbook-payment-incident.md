# Runbook: Payment Incident Response

Last updated: 2026-05-26 | Owner: backend team

---

## Scenario A — User paid but did not receive product

**Symptoms:** User reports bank transfer completed but order still shows "pending".

### Steps

1. **Check order status**
   ```
   GET /admin/orders?status=pending&user_id=<uid>
   ```
   Or query DB:
   ```sql
   SELECT id, ref_code, status, created_at, paid_at FROM orders WHERE user_id = <uid> ORDER BY id DESC LIMIT 5;
   ```

2. **Check webhook_events for the order**
   ```sql
   SELECT * FROM webhook_events WHERE order_id = <order_id>;
   ```
   - Row with `status='matched'` → order was fulfilled. Check user_reports table.
   - Row with `status='amount_mismatch'` → user transferred wrong amount.
   - No row → webhook never fired (bank delay or SePay issue).

3. **Check SePay dashboard**
   - Log into SePay → Transactions → search by ref_code (e.g. `NSQ-XXXXXXXX`).
   - If transaction exists but no webhook_events row → webhook was missed.

4. **Resolution options**

   **Option A — Wait for reconcile cron (preferred)**
   - Cron runs every 15 min, pulls 24h window.
   - Order will be fulfilled automatically on next tick.
   - Confirm by checking `webhook_events` for `provider='reconcile'` after 15 min.

   **Option B — Manual mark-paid (immediate)**
   ```
   POST /admin/orders/<order_id>/mark-paid
   Authorization: Bearer <superuser_token>
   ```
   - This triggers fulfillment immediately.
   - Logs `sepay_tx_id = 'MANUAL-<admin_id>-<order_id>'`.

---

## Scenario B — Refund request

**Trigger:** User requests refund; admin approves.

### Steps

1. **Verify order eligibility**
   - Order must have `status='paid'`.
   - Pending/cancelled/expired orders cannot be refunded via this flow.

2. **Initiate refund via admin panel**
   - Navigate to `/admin/orders/<order_id>`.
   - Click "Hoàn tiền" button → enter reason in confirm dialog → submit.
   - Or via API:
   ```
   POST /admin/orders/<order_id>/refund
   Authorization: Bearer <superuser_token>
   Content-Type: application/json

   {"reason": "User request — product not as described"}
   ```

3. **What happens automatically**
   - `orders.status` → `refunded`; `orders.refunded_at` set to now.
   - `orders.admin_notes` appended with: `{timestamp} [{admin_id}] {reason}`.
   - For **package** orders: `user_profiles.number_download` decremented by quota.
   - For **report** orders: `user_reports.pdf_path` prefixed with `REFUNDED/` (blocks download).
   - Refund email (`order-refund`) sent to user automatically.

4. **Process SePay bank transfer (manual)**
   - Log into SePay dashboard → initiate outbound transfer to user's bank account.
   - SePay processes in 3–5 business days.
   - Note: backend does not automate bank transfer — admin must do this manually.

5. **Verify**
   ```sql
   SELECT id, status, refunded_at, admin_notes FROM orders WHERE id = <order_id>;
   ```
   Check email_outbox for the refund email:
   ```sql
   SELECT status, sent_at FROM email_outbox WHERE template='order-refund' AND user_id=<uid>;
   ```

---

## Scenario C — Reconcile cron failed

**Symptoms:** Sentry alert for `reconcile_sepay` job, or orders stuck pending > 30 min after payment.

### Diagnose

1. **Check Sentry**
   - Filter by `logger:app.jobs.reconcile_sepay` or tag `job=reconcile_sepay`.
   - Common errors: SePay API key expired, DB connection timeout, IntegrityError.

2. **Check scheduler logs**
   ```bash
   docker compose -f deploy/docker-compose.prod.yml logs api --since 1h | grep reconcile
   ```

3. **Check SePay API key**
   ```bash
   curl -H "Authorization: Bearer $SEPAY_API_KEY" \
     "https://my.sepay.vn/userapi/transactions/list?limit=1"
   ```
   Expected: `{"transactions": [...]}`. If 401 → rotate key in SePay dashboard + update `.env.prod`.

### Manual trigger

Run a single reconcile pass without restarting the service:

```bash
# Inside the running container
docker compose -f deploy/docker-compose.prod.yml exec api \
  python -m app.jobs.reconcile_sepay
```

Or from host with venv:
```bash
cd numerology-api
python -m app.jobs.reconcile_sepay
```

Output format:
```
reconcile_sepay done: checked=5 matched=2 fulfilled=2 skipped=0 errors=0
```

### Recovery

- If `errors > 0`: check individual order IDs in logs; use Scenario A > Option B to manually fulfill.
- If SePay API is down: wait for recovery; cron retries every 15 min automatically.
- If scheduler is stuck: restart the API container — scheduler restarts with the app.
  ```bash
  docker compose -f deploy/docker-compose.prod.yml restart api
  ```

---

## Rate Limit Notes

The rate limiter (`app/middleware/rate_limit.py`) uses **in-memory storage** (slowapi default).

**Known tradeoffs — accepted for launch:**

1. **Per-worker isolation.** Gunicorn runs multiple workers (e.g. `-w 4`). Each worker maintains its
   own counter independently. Effective limit for the same IP = `workers × per-route limit`.
   Example: `3/min` login → up to `12/min` effective across 4 workers. Acceptable at current scale.

2. **Reset on restart.** Rate-limit counters are cleared whenever the API container restarts.
   An attacker can abuse this window briefly. Accepted — restart is infrequent.

3. **CF-Connecting-IP only in cloudflare mode.** `TRUSTED_PROXY_MODE=cloudflare` (default) discards
   `X-Forwarded-For` to prevent IP spoofing. If Cloudflare is switched to DNS-only (no proxy),
   set `TRUSTED_PROXY_MODE=direct` so the limiter falls back to `request.client.host` (nginx
   sets `X-Real-IP` correctly, but we use `request.client.host` for safety).

**When to upgrade to Redis-backed storage:**
- Traffic exceeds ~500 req/min sustained, OR
- Multi-region deployment with shared limit requirement.

Switch by changing `Limiter` init in `app/middleware/rate_limit.py`:
```python
from limits.storage import RedisStorage
limiter = Limiter(
    key_func=_cf_ip_key,
    storage_uri="redis://redis:6379",
    ...
)
```
Then add a Redis service to `deploy/docker-compose.prod.yml`.

---

## Key DB Queries Reference

```sql
-- Pending orders older than 15 min (likely missed webhook)
SELECT id, ref_code, total_amount, created_at
FROM orders
WHERE status = 'pending' AND created_at < now() - interval '15 minutes'
ORDER BY created_at DESC;

-- Recent webhook events
SELECT provider, sepay_tx_id, status, ref_code, amount, created_at
FROM webhook_events
ORDER BY id DESC LIMIT 20;

-- Refunded orders today
SELECT id, ref_code, refunded_at, admin_notes
FROM orders
WHERE status = 'refunded' AND refunded_at >= current_date;
```
