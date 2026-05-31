# Runbook: Go-Live Deployment

Last updated: 2026-05-26 | Owner: backend team

---

## Pre-flight Checklist

Thực hiện toàn bộ 16 mục trước khi bắt đầu deploy. Tick từng mục sau khi xác nhận.

| # | Hạng mục | Cách kiểm tra | Done |
|---|----------|---------------|------|
| 1 | Backup DB mới nhất < 24 giờ | `ls -lt /opt/backups/postgres/` — timestamp < 24h | [ ] |
| 2 | Restore test pass | Chạy restore vào DB staging, verify row count khớp | [ ] |
| 3 | Sentry quiet 24h | Sentry dashboard → 0 unresolved issues mới trong 24h | [ ] |
| 4 | UptimeRobot 100% 24h | UptimeRobot → uptime log 24h = 100% | [ ] |
| 5 | SSL Labs grade A | [ssllabs.com/ssltest](https://www.ssllabs.com/ssltest/) → `nhansinhquan.vn` | [ ] |
| 6 | securityheaders.com grade A | [securityheaders.com](https://securityheaders.com) → `nhansinhquan.vn` | [ ] |
| 7 | Lighthouse mobile ≥ 85 | `npx lighthouse https://nhansinhquan.vn --form-factor=mobile` | [ ] |
| 8 | DNS Cloudflare proxy bật (cam) | Cloudflare dashboard → `@`, `www`, `api` đều cam | [ ] |
| 9 | Sitemap đã submit GSC | Google Search Console → Sitemaps → Submitted | [ ] |
| 10 | Email mail-tester ≥ 9/10 | Gửi email thử → [mail-tester.com](https://www.mail-tester.com) | [ ] |
| 11 | Reconcile cron chạy ok | Logs: `docker compose logs api | grep reconcile` — không có error | [ ] |
| 12 | Refund flow tested | Tạo order test → mark-paid → refund → verify email gửi | [ ] |
| 13 | Rate limit verified | `curl -X POST .../auth/login` × 6 → response 6 = 429 | [ ] |
| 14 | Turnstile hoạt động | Checkout flow real browser, không bypass captcha | [ ] |
| 15 | Legal pages accessible | `/chinh-sach-bao-mat`, `/dieu-khoan-dich-vu`, `/chinh-sach-hoan-tien` → 200 | [ ] |
| 16 | [PLACEHOLDER] điền biến môi trường prod | `.env.prod` — verify SENTRY_DSN, SEPAY_API_KEY, RESEND_API_KEY, SECRET_KEY đã set | [ ] |

> Nếu bất kỳ mục nào fail: STOP, fix, re-check trước khi tiếp tục.

---

## Deploy Steps

Thực hiện tuần tự. Không bỏ bước.

### 1. SSH vào VPS

```bash
ssh deploy@[VPS_IP]
# hoặc
ssh -i ~/.ssh/numerology_deploy deploy@[VPS_IP]
```

### 2. Vào thư mục dự án

```bash
cd /opt/numerology
```

### 3. Pull code mới nhất

```bash
git pull origin main
# Verify commit hash khớp với CI build đã pass
git log --oneline -3
```

### 4. Pull Docker images mới

```bash
cd numerology-api
docker compose -f docker-compose.prod.yml pull
```

### 5. Build và khởi động API

```bash
docker compose -f docker-compose.prod.yml up -d --build api
```

### 6. Chạy DB migration

```bash
docker compose -f docker-compose.prod.yml exec api alembic upgrade head
# Verify migration mới nhất đã được apply:
docker compose -f docker-compose.prod.yml exec api alembic current
```

### 7. Restart API để reload scheduler + Sentry

```bash
docker compose -f docker-compose.prod.yml restart api
```

### 8. Smoke test health

```bash
curl -s https://cms.nhansinhquan.vn/health/detail | python3 -m json.tool
# Expect: {"status": "ok", "db": "ok", "scheduler": "running"}
```

### 9. Build frontend

```bash
cd /opt/numerology/Numerology-Landing-Page
npm ci --prefer-offline
npm run build
npm run postbuild   # sitemap gen, robots.txt copy
```

### 10. Restart frontend service

```bash
# Nếu dùng PM2:
pm2 restart numerology-frontend
# Nếu dùng systemd:
sudo systemctl restart numerology-frontend
```

### 11. Submit sitemap mới lên GSC

- Google Search Console → Sitemaps → nhập `https://nhansinhquan.vn/sitemap.xml` → Submit

### 12. Test end-to-end flow thật

Chạy 1 flow hoàn chỉnh trên production (dùng tài khoản test):

1. Register tài khoản mới
2. Vào /shop → chọn sản phẩm → checkout
3. Chuyển khoản thật (số tiền nhỏ nhất) → verify order status → `paid`
4. Kiểm tra email nhận được (invoice + download link)
5. Download báo cáo PDF → mở thành công
6. Admin panel → verify order hiển thị đúng

---

## Rollback Triggers

Kích hoạt rollback ngay khi phát hiện bất kỳ điều kiện nào sau:

| Điều kiện | Ngưỡng | Hành động |
|-----------|--------|-----------|
| Error rate tăng đột biến | > 5% requests lỗi trong 5 phút | Rollback ngay |
| Uptime drop | UptimeRobot báo fail 2 lần liên tiếp | Rollback ngay |
| Payment flow fail | SePay webhook 0 received > 15 phút (giờ cao điểm) | Kiểm tra trước, rollback nếu cần |
| Bug critical user-reported | Mất dữ liệu, không login được, không checkout được | Rollback ngay |
| Sentry spike | > 50 new errors trong 10 phút | Rollback ngay |

---

## Rollback Procedure

```bash
# 1. Checkout tag stable trước đó
cd /opt/numerology
git fetch --tags
git checkout tags/v[PREVIOUS_TAG]

# 2. Rebuild API từ tag cũ
cd numerology-api
docker compose -f docker-compose.prod.yml up -d --build api

# 3. Downgrade DB nếu migration mới gây lỗi
docker compose -f docker-compose.prod.yml exec api alembic downgrade -1
# Verify:
docker compose -f docker-compose.prod.yml exec api alembic current

# 4. Restart
docker compose -f docker-compose.prod.yml restart api

# 5. Build frontend từ tag cũ
cd /opt/numerology/Numerology-Landing-Page
npm run build && npm run postbuild
pm2 restart numerology-frontend

# 6. Verify health
curl -s https://cms.nhansinhquan.vn/health/detail
```

> Sau rollback: mở Sentry, filter theo timeframe rollback, tìm root cause trước khi re-deploy.

---

## Comms Plan

### Trước launch (T-24h)

- Email tới beta list: "Chúng tôi chuẩn bị ra mắt chính thức vào [ngày]. Cảm ơn bạn đã đồng hành."
- Zalo OA: post announcement với link landing page
- Facebook page: post teaser (không nêu giờ cụ thể để tránh spike)

### Sau launch thành công (T+1h)

- Email to all beta users: "Nhân Sinh Quan đã chính thức ra mắt — [link mua]"
- Zalo OA: "Chính thức mở cửa. Ưu đãi ra mắt: [offer]"
- Facebook: post đầy đủ với ảnh + link

### Nếu rollback

- Email ngắn: "Chúng tôi phát hiện một sự cố kỹ thuật và đang xử lý. Dịch vụ sẽ trở lại trong [X] giờ. Xin lỗi vì sự bất tiện."
- Tạm dừng mọi quảng cáo đang chạy
- Zalo OA: đồng nội dung với email
- Không đưa chi tiết kỹ thuật ra ngoài

---

## Liên hệ khẩn cấp

| Vai trò | Tên | Liên hệ |
|---------|-----|---------|
| Dev Lead | [DEV_LEAD_NAME] | [DEV_LEAD_PHONE] |
| DevOps | [DEVOPS_NAME] | [DEVOPS_PHONE] |
| Business Owner | [OWNER_NAME] | [OWNER_PHONE] |

> Điền thông tin thật trước go-live.
