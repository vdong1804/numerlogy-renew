# Post-Launch Monitoring Runbook

Last updated: 2026-05-26 | Owner: backend team

---

## Dashboard Links

| Tool | URL | Dùng để |
|------|-----|---------|
| Sentry | [SENTRY_PROJECT_URL] | Error tracking, stack traces, alert rules |
| UptimeRobot | [UPTIMEROBOT_DASHBOARD_URL] | Uptime %, response time, incident log |
| GA4 Realtime | [GA4_REALTIME_URL] | Active users, conversion events, traffic source |
| Google Search Console | [GSC_URL] | Indexing status, Core Web Vitals, search performance |
| SePay Dashboard | https://my.sepay.vn | Transaction log, webhook status, reconcile |
| Resend Dashboard | https://resend.com/emails | Email delivery, bounce rate, spam complaints |

> Điền URL thật sau khi setup xong. Bookmark tất cả vào browser admin.

---

## Daily Checks (5 phút/ngày)

Thực hiện mỗi sáng, ưu tiên trước 10:00.

### 1. Sentry — new issues

- Mở Sentry → Issues → filter "Last 24h", "Unresolved"
- Target: 0 issues mới. Nếu có: triage severity (P0/P1/P2)
- Xem số lượng event/issue, không chỉ presence

### 2. UptimeRobot — uptime %

- Mở dashboard → xem uptime % 24h cho `nhansinhquan.vn` và `cms.nhansinhquan.vn`
- Target: 100%. Nếu < 99.9%: check incident log, tìm nguyên nhân

### 3. Resend — bounce rate

- Resend dashboard → Emails → filter 24h
- Target bounce rate < 2%. Nếu > 5%: xem ngay (xem mục Alert Thresholds)

### 4. SePay — transaction success rate

- SePay dashboard → Transactions → filter hôm nay
- Đếm matched/total. Target: 0 failed webhook (cron reconcile xử lý tự động)
- Nếu 0 transaction trong giờ cao điểm (9-12h, 19-22h): kiểm tra webhook_events table

```sql
-- Kiểm tra webhook events 24h qua
SELECT provider, status, count(*) as cnt
FROM webhook_events
WHERE created_at >= now() - interval '24 hours'
GROUP BY provider, status
ORDER BY cnt DESC;
```

---

## Weekly Checks (30 phút/tuần — mỗi thứ Hai)

### 1. Slow query log review

```bash
docker compose -f docker-compose.prod.yml logs api --since 168h | grep "slow_query"
```

Hoặc từ Postgres:
```sql
SELECT query, mean_exec_time, calls
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;
```

Target: không có query > 500ms thường xuyên.

### 2. DB size growth

```sql
SELECT pg_size_pretty(pg_database_size('numerology_prod')) AS db_size;
SELECT relname, pg_size_pretty(pg_total_relation_size(relid)) AS size
FROM pg_catalog.pg_statio_user_tables
ORDER BY pg_total_relation_size(relid) DESC
LIMIT 10;
```

Target: tăng trưởng hợp lý (< 500MB/tháng ở giai đoạn đầu).

### 3. Top 10 errors trend

- Sentry → Issues → sort by "Events" (7 ngày)
- So sánh với tuần trước: errors mới hay tăng đột biến?
- Assign và fix P0/P1 trong tuần

### 4. Conversion funnel (GA4)

- GA4 → Explorations → Funnel: `page_view(/shop)` → `begin_checkout` → `purchase`
- Target: conversion rate ≥ 3% (shop → purchase)
- Nếu drop tại bước nào: điều tra UX hoặc lỗi kỹ thuật

---

## Alert Thresholds

### Sentry

| Condition | Action |
|-----------|--------|
| > 10 unique errors/giờ | Page dev lead ngay |
| Error rate > 5% requests | Xem xét rollback (xem go-live-runbook.md) |
| New issue severity "fatal" | Page ngay, không chờ |

Cấu hình alert trong Sentry: Project Settings → Alerts → New Alert Rule.

### UptimeRobot

| Condition | Action |
|-----------|--------|
| 2 consecutive check fails | Email + SMS tự động (đã cấu hình trong UptimeRobot) |
| Downtime > 5 phút | Dev lead check ngay |
| Response time > 3s sustained | Investigate DB / infra |

### Resend (Email delivery)

| Condition | Action |
|-----------|--------|
| Bounce rate > 5% | Review danh sách, clean invalid emails |
| Spam complaint rate > 0.1% | Review email content, unsubscribe flow |
| Delivery rate < 95% | Check SPF/DKIM, liên hệ Resend support |

### SePay Webhook

| Condition | Action |
|-----------|--------|
| 0 webhook received trong 30 phút (giờ cao điểm) | Check SePay dashboard → có transaction không? |
| Reconcile cron báo errors > 0 | Xem Scenario C trong runbook-payment-incident.md |
| amount_mismatch events tăng | Review QR code / hướng dẫn thanh toán với user |

> Lưu ý: 0 webhook ngoài giờ cao điểm (ví dụ 2-6h sáng) là bình thường.

---

## Escalation Contacts

| Vai trò | Tên | Kênh liên hệ | Giờ phản hồi |
|---------|-----|-------------|-------------|
| Dev Lead | [DEV_LEAD_NAME] | [DEV_LEAD_PHONE] / Zalo | < 30 phút (P0), < 4h (P1) |
| DevOps | [DEVOPS_NAME] | [DEVOPS_PHONE] / Zalo | < 1h (P0), < 8h (P1) |
| Business Owner | [OWNER_NAME] | [OWNER_PHONE] | Thông báo khi downtime > 15 phút |

**Severity definitions:**

- P0 — Production down hoặc payment broken (wake up at 3am)
- P1 — Core feature broken, ảnh hưởng > 10% users (fix trong ngày)
- P2 — Non-critical bug, workaround có thể dùng (fix trong tuần)

---

## Common Incident Playbooks

| Tình huống | Tài liệu tham khảo |
|-----------|-------------------|
| User paid nhưng chưa nhận sản phẩm | [runbook-payment-incident.md — Scenario A](./runbook-payment-incident.md#scenario-a--user-paid-but-did-not-receive-product) |
| Yêu cầu hoàn tiền | [runbook-payment-incident.md — Scenario B](./runbook-payment-incident.md#scenario-b--refund-request) |
| Reconcile cron lỗi | [runbook-payment-incident.md — Scenario C](./runbook-payment-incident.md#scenario-c--reconcile-cron-failed) |
| Deploy fail / rollback | [go-live-runbook.md — Rollback Procedure](./go-live-runbook.md#rollback-procedure) |

---

## First 30 Days Post-Launch — Review Schedule

| Ngày | Việc cần làm |
|------|-------------|
| D+1 | Daily check + review GA4 realtime, Sentry 24h |
| D+3 | Triage beta feedback P0/P1, deploy hotfix nếu cần |
| D+7 | First weekly check, so sánh conversion funnel với target |
| D+14 | DB growth review, slow query analysis |
| D+30 | Full monthly review: uptime %, error trend, revenue vs target, conversion |
