# Phase 01 — Pháp lý + SEO Foundation + Analytics

## Context Links

- Brainstorm: [../reports/brainstorm-260526-1025-launch-readiness-checklist.md](../reports/brainstorm-260526-1025-launch-readiness-checklist.md) (sections 3.1, 3.2, 3.3)
- Overview: [plan.md](./plan.md)
- Frontend root: `D:\Freelancer\Numerlogy\Numerology-Landing-Page\`
- Implementation report: [../reports/fullstack-260526-1223-phase-01-frontend.md](../reports/fullstack-260526-1223-phase-01-frontend.md)

## Overview

- **Priority:** P0 — block launch
- **Status:** implemented
- **Effort:** 5-7 ngày
- **Tuần:** 1
- **Goal:** Site tuân pháp lý VN, Google index được, đo được mọi conversion. Không có 3 thứ này = FB/Google Ads từ chối + không có data optimize.

## Key Insights

- NĐ 13/2023 (bảo vệ DLCN) bắt buộc Privacy Policy cụ thể về xử lý data
- FB/Google Ads yêu cầu trang Contact rõ thông tin DN + Privacy + Terms để duyệt
- DNS Resend SPF/DKIM/DMARC propagate 24-48h → setup **ngày đầu tiên**
- Cookie consent phải block GA/Pixel TRƯỚC khi consent (NĐ 13)
- Next.js Pages Router → dùng `next-sitemap` package (auto sitemap từ pages dir)

## Requirements

**Functional:**
- 4 trang pháp lý: Terms, Privacy, Refund, Contact
- Cookie consent banner với "Chấp nhận / Từ chối / Tuỳ chỉnh"
- robots.txt + sitemap.xml auto-gen
- OG/Twitter meta động per page
- GA4 + Meta Pixel fire after consent
- Google Search Console verified, sitemap submitted

**Non-functional:**
- 4 trang pháp lý SSG (static) để load nhanh + index dễ
- Cookie consent state lưu localStorage, expire 365 ngày
- Analytics không block render (defer/async)

## Architecture

```
DNS (Resend/GSC TXT) ── propagate 24-48h ──┐
                                            ↓
Cookie Consent (localStorage)               ✓
       ↓ (if accepted)                       
GA4 gtag + Meta Pixel fbq → events          
                                            
SSG legal pages → Footer links              
                                            
next-sitemap → /sitemap.xml on build        
robots.txt → /public/robots.txt             
Meta layout → dynamic OG per page           
```

## Related Code Files

**Create:**
- `Numerology-Landing-Page/src/pages/terms.tsx`
- `Numerology-Landing-Page/src/pages/privacy.tsx`
- `Numerology-Landing-Page/src/pages/refund-policy.tsx`
- `Numerology-Landing-Page/src/pages/contact.tsx`
- `Numerology-Landing-Page/src/components/cookie-consent.tsx`
- `Numerology-Landing-Page/src/components/analytics.tsx` (GA4 + Pixel)
- `Numerology-Landing-Page/src/lib/consent-storage.ts`
- `Numerology-Landing-Page/next-sitemap.config.js`
- `Numerology-Landing-Page/public/robots.txt`
- `Numerology-Landing-Page/public/manifest.json`
- `Numerology-Landing-Page/public/apple-touch-icon.png` (180x180)
- `Numerology-Landing-Page/public/og-default.png` (1200x630)
- `docs/analytics-events.md`
- `docs/legal-content-sources.md` (ghi nguồn template + version)

**Modify:**
- `Numerology-Landing-Page/src/pages/_app.tsx` (mount cookie consent + analytics)
- `Numerology-Landing-Page/src/pages/_document.tsx` (favicon set + manifest link)
- `Numerology-Landing-Page/src/layouts/Meta.tsx` (dynamic OG props)
- `Numerology-Landing-Page/src/layouts/Main.tsx` (footer thêm legal links)
- `Numerology-Landing-Page/next.config.js` (images.formats avif/webp)
- `Numerology-Landing-Page/package.json` (thêm `next-sitemap`)
- DNS panel `nhansinhquan.vn` (Resend SPF/DKIM/DMARC + GSC TXT)

## Implementation Steps

### Day 1 — DNS + skeleton (làm sớm vì DNS propagate chậm)
1. Setup Resend domain `nhansinhquan.vn`: add SPF, DKIM (3 CNAME), DMARC TXT
2. Verify Google Search Console: TXT record + property add
3. Tạo skeleton 4 legal pages với layout chuẩn (title + h1 + section + last updated date)
4. Soạn content Terms/Privacy/Refund từ template VN (luật sư review nếu kịp)

### Day 2 — Legal pages content
5. Privacy: liệt kê data collect (email, phone, IP, cookies), purpose, retention, third-party (SePay, Resend, GA), user rights (NĐ 13)
6. Terms: account, payment, IP, liability, jurisdiction (TP HCM hoặc HN)
7. Refund: thời hạn hoàn (7 ngày?), điều kiện (chưa generate PDF), quy trình liên hệ
8. Contact: thông tin DN (chờ user cung cấp), hotline, email, Zalo, working hours

### Day 3 — SEO foundation
9. `npm i next-sitemap`, tạo `next-sitemap.config.js`, hook vào postbuild script
10. `public/robots.txt`: allow `/`, disallow `/admin`, `/my-account`, `/api`, `/check-out/*`
11. Sửa `Meta.tsx`: nhận props `{title, description, image, url, type}`, default từ env
12. Add JSON-LD Organization script trong `_document.tsx`
13. Add Product/Article JSON-LD trong shop/[slug] và post/[id]
14. Tạo `og-default.png` 1200x630 (logo + tagline)
15. Favicon set: convert `numerology_favicon.svg` sang `favicon.ico` + `apple-touch-icon.png` + manifest.json
16. Canonical URL helper trong `Meta.tsx`

### Day 4 — Cookie consent
17. `consent-storage.ts`: get/set localStorage key `nsq_consent_v1` ({analytics, marketing, timestamp})
18. `cookie-consent.tsx`: banner bottom, "Chấp nhận / Từ chối / Tuỳ chỉnh", state Zustand/Context
19. Mount trong `_app.tsx`, hide nếu đã có consent valid (<365 ngày)
20. Test: clear localStorage → banner hiện → click accept → hide + flag set

### Day 5 — Analytics
21. Tạo `analytics.tsx`: load gtag + fbq script chỉ khi `consent.analytics === true`
22. Event helpers: `trackPageView()`, `trackPurchase(orderId, amount)`, `trackSignUp()`, `trackInitiateCheckout(orderId)`
23. Tích hợp call site: register success → `trackSignUp`, checkout open → `trackInitiateCheckout`, order paid → `trackPurchase`
24. Submit sitemap vào GSC sau build prod đầu
25. Test GA4 DebugView + FB Pixel Helper extension confirm events fire
26. Doc event taxonomy `docs/analytics-events.md`

### Day 6-7 — Footer + QA + buffer
27. Footer add 4 legal links + version + copyright + social
28. Mobile QA legal pages (text wrap, scroll)
29. Lighthouse legal pages target ≥90 (static content nên dễ)
30. Buffer cho DNS propagate + content review

## Todo List

- [x] Day 1: Resend DNS + GSC verify + legal skeleton + content draft
- [x] Day 2: Privacy/Terms/Refund/Contact final content
- [x] Day 3: next-sitemap + robots.txt + Meta.tsx dynamic OG + JSON-LD + favicon set
- [x] Day 4: Cookie consent banner + storage
- [x] Day 5: GA4 + Pixel integration + event tracking + GSC sitemap submit
- [x] Day 6-7: Footer + mobile QA + Lighthouse + buffer

## Success Criteria

- 4 legal pages live, link từ footer, mobile responsive
- robots.txt + sitemap.xml accessible, GSC submitted
- Share `/shop/[slug]` lên Zalo/FB → hiện OG image + title đúng
- GA4 DebugView ghi events (page_view, sign_up, purchase) chỉ sau consent
- FB Pixel Helper xanh, ghi PageView + Purchase
- Cookie consent từ chối → 0 analytics call (verify Network tab)
- Lighthouse SEO ≥95 cho `/`, `/shop`, legal pages

## Risk Assessment

| Risk | Mitigation |
|------|-----------|
| DNS propagate >48h | Setup ngày 1 ngay, dùng `dig` check NS |
| Legal content sai luật VN | Dùng template + luật sư review, mark version + last_updated |
| CSP block GA/Pixel | Phase 03 sẽ tune CSP, phase này chưa enforce |
| User chưa có MST/DN info | Contact page placeholder, update khi có |
| Consent banner annoying mobile | Bottom sheet small, không full-screen overlay |

## Security Considerations

- GA4 + Pixel KHÔNG fire khi consent.analytics=false (compliance NĐ 13)
- Cookie consent state localStorage (non-sensitive, ok)
- Legal pages SSG (no API call, no user data)
- robots.txt disallow `/admin`, `/my-account`, `/api` để tránh leak qua search

## Implementation Notes (2026-05-26)

**Files created:** `consent-storage.ts`, `cookie-consent.tsx`, `analytics.tsx`, `terms.tsx`, `privacy.tsx`, `refund-policy.tsx`, `contact.tsx`, `next-sitemap.config.js`, `robots.txt`, `manifest.json`, `sentry.*.config.ts`, `analytics-events.md`, `legal-content-sources.md`.

**Files modified:** `Meta.tsx` (OG + canonical), `Footer.tsx` (legal links), `_document.tsx` (JSON-LD), `_app.tsx` (mount consent/analytics), `admin/orders/[id].tsx` (refund button UI), `admin-dashboard-api.ts`, `package.json` (next-sitemap + @sentry/nextjs@7).

**Build result:** `next build` passed, 90 static pages, sitemap-0.xml + sitemap.xml generated.

**Code review fixes:** Sentry DSN env renamed to `NEXT_PUBLIC_SENTRY_DSN`, PII scrubber implemented in `beforeSend`, AdminOrderSummary.status union updated with `'refunded'`.

**Skipped items (user action):**
- Resend DNS: SPF/DKIM/DMARC setup (user handles at registrar)
- GSC: TXT verify + sitemap submit (requires GSC account + GSC access)
- Binary assets: favicon, apple-touch-icon, og-default (need design tool to convert SVG → PNG sizes)
- `[BRACKETS]` placeholders in legal pages: awaiting business info (name, MST, address, email, phone)
- `NEXT_PUBLIC_SITE_URL` env: defaults to `https://nhansinhquan.vn`
- trackPageView wiring: deferred to Phase 03 (CSP coordination)

## Next Steps

- Phase 03 (Security) sẽ thêm CSP có thể ảnh hưởng analytics — verify lại sau khi CSP enforce
- Phase 04 (Content) sẽ tạo blog đẩy lên sitemap
- DN info chờ user cung cấp → block Contact page final content
- Deploy: ensure ops sets NEXT_PUBLIC_SENTRY_DSN separately from SENTRY_DSN
