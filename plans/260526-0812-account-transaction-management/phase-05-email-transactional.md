# Phase 05 — Email Transactional (Resend + Outbox)

## Context Links
- [Plan overview](./plan.md)
- [Phase 02](./phase-02-sepay-integration-fulfillment.md) — fulfillment trigger emails
- Resend docs: https://resend.com/docs

## Overview
- **Priority:** P1 (UX polish, reduce support load)
- **Status:** pending
- **Duration:** Tuần 6 (5 ngày dev)
- **Description:** Email transactional qua Resend với outbox pattern (retry-safe). 6 template chính: welcome, order_paid, order_expired, quota_low, package_expiring, password_reset (refactor cũ). Background worker dispatch mỗi 1 phút.

## Key Insights
- `email_service.py` đã có (dùng cho password reset) → refactor thành provider-agnostic
- Outbox pattern: insert vào `email_outbox` thay vì gửi sync → cron dispatch → retry exponential backoff
- Resend free tier: 100/day, 3000/month, domain verified required (else send-from `onboarding@resend.dev`)
- Domain `nhansinhquan.vn` user có DNS access → setup SPF + DKIM + DMARC

## Requirements

### Functional
- 6 email templates Jinja2 (HTML + plain text fallback):
  1. `welcome.html` — sau đăng ký, kèm link tải lead magnet
  2. `order_paid.html` — mua thành công, kèm link đơn + download report
  3. `order_expired.html` — đơn pending quá 30 phút → tự cancel + email
  4. `quota_low.html` — quota còn <20%
  5. `package_expiring.html` — gói hết hạn trong 3 ngày
  6. `password_reset.html` — refactor template cũ, chuẩn hóa
- Outbox table `email_outbox` (đã tạo Phase 01)
- Worker dispatch mỗi 1 phút (cron hoặc APScheduler)
- Retry: max 5 lần, exponential backoff (1m, 5m, 15m, 1h, 6h)
- Respect user notification_prefs (Phase 03 settings)
- Unsubscribe link → toggle pref off

### Non-functional
- Send rate <100/day initially (Resend free tier)
- Email open rate trackable (Resend webhook optional Phase 2)
- All emails Vietnamese language, mobile-friendly HTML

## Architecture

### Outbox flow

```
Event (register/paid/expire/quota_low) → email_service.enqueue(template, to, payload)
                                          └─ INSERT email_outbox (status=pending)

Cron 1 phút:
  email_dispatcher.run()
    SELECT * FROM email_outbox 
      WHERE status='pending' 
        AND (attempts=0 OR next_retry_at <= NOW())
      LIMIT 50
      FOR UPDATE SKIP LOCKED
    
    For each:
      Try send via provider (Resend API)
      Success → status='sent', sent_at=NOW
      Fail   → attempts++, next_retry_at=NOW+backoff(attempts)
              if attempts >= 5 → status='failed', alert admin
```

### Backend structure

```
numerology-api/app/
├── services/
│   ├── email_service.py        # REFACTOR: provider-agnostic enqueue
│   ├── email_providers/
│   │   ├── __init__.py
│   │   ├── base.py             # NEW: EmailProvider abstract
│   │   ├── resend_provider.py  # NEW
│   │   └── smtp_provider.py    # NEW (fallback)
│   └── email_dispatcher.py     # NEW: cron worker
├── templates/emails/
│   ├── base.html               # NEW: shared layout
│   ├── welcome.html            # NEW
│   ├── order-paid.html         # NEW
│   ├── order-expired.html      # NEW
│   ├── quota-low.html          # NEW
│   ├── package-expiring.html   # NEW
│   └── password-reset.html     # REFACTOR
├── routers/
│   └── unsubscribe.py          # NEW: GET /unsubscribe?token=...
└── jobs/
    └── email_dispatcher_job.py # NEW: entry point cho cron
```

### Config
```
# .env additions
EMAIL_PROVIDER=resend  # or 'smtp'
RESEND_API_KEY=re_xxx
EMAIL_FROM=no-reply@nhansinhquan.vn
EMAIL_FROM_NAME=Nhân Sinh Quan
EMAIL_REPLY_TO=support@nhansinhquan.vn

# SMTP fallback
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=...
SMTP_PASS=...
```

### Trigger points

| Event | Where to enqueue |
|-------|------------------|
| Register success | `routers/auth.py` register handler |
| Order paid | `services/fulfillment_service.py` cuối hàm fulfill |
| Order expired | `jobs/expire_pending_orders_job.py` (Phase 06) |
| Quota low | `jobs/check_quota_warnings_job.py` (Phase 06) |
| Package expiring | `jobs/check_package_expiry_job.py` (Phase 06) |
| Password reset | `services/password_reset_service.py` (existing) |

## Related Code Files

### Create
- `numerology-api/app/services/email_providers/__init__.py`
- `numerology-api/app/services/email_providers/base.py`
- `numerology-api/app/services/email_providers/resend_provider.py`
- `numerology-api/app/services/email_providers/smtp_provider.py`
- `numerology-api/app/services/email_dispatcher.py`
- `numerology-api/app/jobs/__init__.py`
- `numerology-api/app/jobs/email_dispatcher_job.py`
- `numerology-api/app/routers/unsubscribe.py`
- `numerology-api/app/templates/emails/base.html`
- `numerology-api/app/templates/emails/welcome.html`
- `numerology-api/app/templates/emails/order-paid.html`
- `numerology-api/app/templates/emails/order-expired.html`
- `numerology-api/app/templates/emails/quota-low.html`
- `numerology-api/app/templates/emails/package-expiring.html`
- `numerology-api/app/utils/unsubscribe_token.py` — signed token (HMAC + user_id + pref_key)
- `numerology-api/tests/test_email_service.py`
- `numerology-api/tests/test_email_dispatcher.py`
- `numerology-api/scripts/test_send_email.py` — manual smoke test
- `docs/email-setup-runbook.md` — DNS records + Resend onboarding

### Modify
- `numerology-api/app/services/email_service.py` — refactor thành provider-agnostic + enqueue
- `numerology-api/app/services/password_reset_service.py` — dùng email_service.enqueue thay vì sync send
- `numerology-api/app/services/fulfillment_service.py` — enqueue order_paid email cuối fulfill
- `numerology-api/app/routers/auth.py` — enqueue welcome email sau register
- `numerology-api/app/templates/emails/password-reset.html` — refactor extend base
- `numerology-api/app/config.py` — add EMAIL_* + RESEND_* + SMTP_* settings
- `numerology-api/app/main.py` — register unsubscribe router
- `numerology-api/.env.example` — add email vars
- `numerology-api/deploy/docker-compose.prod.yml` — service `email-worker` chạy cron (hoặc dùng APScheduler trong-process)

## Implementation Steps

1. **DNS setup** (user, song song dev):
   - Resend dashboard → Add domain `nhansinhquan.vn`
   - Add TXT records: SPF (`v=spf1 include:_spf.resend.com ~all`), DKIM (3 CNAME records từ Resend), DMARC (`v=DMARC1; p=quarantine; rua=mailto:dmarc@nhansinhquan.vn`)
   - Wait 24-48h propagation
2. **Config additions** — `.env.example` + `config.py` Settings class
3. **EmailProvider abstract** — `send(to, subject, html, text) -> {message_id, error}`
4. **ResendProvider** — `httpx.AsyncClient.post('https://api.resend.com/emails', ...)` với API key
5. **SMTPProvider** — `aiosmtplib` fallback
6. **`email_service.enqueue(template, to, payload, user_id=None)`** — render template với Jinja2 → INSERT email_outbox
7. **`email_dispatcher.run()`** — main loop: select pending, FOR UPDATE SKIP LOCKED, send qua provider, update status
8. **Backoff helper** — `next_retry_at(attempts)` returns delta phút [1, 5, 15, 60, 360]
9. **Job entry `email_dispatcher_job.py`** — standalone async script chạy mỗi 1 phút (cron hoặc APScheduler)
10. **Template `base.html`** — Vietnamese layout, logo, footer với unsubscribe link, mobile-friendly inline CSS
11. **Templates 6 emails** — extends base, render với payload context
12. **Unsubscribe** — `utils/unsubscribe_token.py`: sign `(user_id, pref_key)` với HMAC + EMAIL_SECRET; router decode + toggle off
13. **Refactor `password_reset_service.py`** → enqueue thay vì sync send
14. **Trigger enqueue** ở fulfillment + auth register
15. **Tests** — enqueue insert đúng, dispatch retry với backoff, provider mock send, unsubscribe token valid/invalid
16. **`scripts/test_send_email.py`** — CLI: `python scripts/test_send_email.py welcome --to test@example.com` để smoke test
17. **Deploy worker** — docker-compose service `email-worker` chạy `python -m app.jobs.email_dispatcher_job` với restart=always; HOẶC tích hợp APScheduler vào FastAPI app (đơn giản hơn nhưng share resources)
18. **Manual test** — register user → check inbox welcome; mua đơn → check inbox order_paid; click unsubscribe → verify pref off

## Todo List

- [ ] M1. DNS records nhansinhquan.vn cho Resend (user task, làm sớm)
- [ ] M2. Config EMAIL_PROVIDER + .env.example
- [ ] M3. EmailProvider abstract + ResendProvider + SMTPProvider
- [ ] M4. email_service.enqueue refactor
- [ ] M5. email_dispatcher worker + backoff logic
- [ ] M6. Job entry email_dispatcher_job.py
- [ ] M7. Template base.html + 6 email templates
- [ ] M8. Unsubscribe utils + router
- [ ] M9. Refactor password_reset_service dùng enqueue
- [ ] M10. Trigger enqueue ở fulfillment + auth register
- [ ] M11. Tests test_email_service + test_email_dispatcher
- [ ] M12. CLI script test_send_email.py
- [ ] M13. Deploy worker setup (docker-compose hoặc APScheduler in-process)
- [ ] M14. Manual smoke test 6 emails
- [ ] M15. Docs email-setup-runbook.md

## Success Criteria

- DNS verified ở Resend dashboard (green checkmarks SPF/DKIM/DMARC)
- Register user → welcome email arrive trong 2 phút, không spam folder
- Mua đơn → order_paid email arrive với link download báo cáo
- Email dispatcher retry 5 lần nếu fail, sau đó status=failed + admin alert
- Unsubscribe link click → pref toggled, future emails skip
- All templates render đúng tiếng Việt UTF-8, mobile readable
- Resend dashboard hiện stats: sent count, delivered rate ≥95%

## Risk Assessment

| Risk | Mức | Mitigation |
|------|-----|-----------|
| DNS chưa propagate → Resend reject send | Cao | Làm DNS sớm (24-48h trước phase 5); dùng SMTPProvider fallback hoặc Resend sandbox cho dev |
| Email vào spam folder | Cao | SPF + DKIM + DMARC đúng; warm-up từ từ <50/ngày tuần đầu; tránh keyword spam trong subject |
| Outbox table grow vô hạn | TB | Cron Phase 6 xóa rows `status=sent AND sent_at < NOW - 30 days` |
| Concurrent dispatchers double-send | Cao | `FOR UPDATE SKIP LOCKED` trong query, only 1 worker chạy |
| Resend free tier hết quota (100/day) | TB | Monitor count; nếu vượt → fallback SMTP hoặc upgrade Resend paid |
| User unsubscribe token leak | TB | Token HMAC signed, expire 30 ngày; revoke khi user đổi pref qua UI |
| Email template typo Vietnamese diacritics | TB | Test render 6 templates với data thật trước go-live |

## Security Considerations

- API key Resend lưu env, KHÔNG commit
- Unsubscribe token: HMAC-SHA256 với EMAIL_SECRET (separate from JWT_SECRET), include user_id + pref_key + expiry
- KHÔNG include sensitive data trong email (vd full address, phone) trừ khi cần thiết
- Email content escape HTML để tránh injection (Jinja2 autoescape ON)
- Webhook unsubscribe rate limit 10 req/phút/IP
- Email outbox payload có thể chứa PII → encrypt at rest nếu yêu cầu compliance (Phase 2+)

## Next Steps
- Parallel với Phase 03, 04
- Phase 06 add 3 cron jobs trigger emails (expire orders, quota low, package expiring)
- Phase 7 verify deliverability rate trước go-live
