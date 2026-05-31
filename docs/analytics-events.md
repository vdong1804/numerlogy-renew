# Analytics Event Taxonomy

**Platform:** GA4 + Meta Pixel  
**Consent gate:** All events fire ONLY after `nsq_consent_v1.analytics = true` (GA4) or `nsq_consent_v1.marketing = true` (Pixel)

---

## Events

| Event Name | GA4 | Pixel | Trigger Point | Parameters |
|---|---|---|---|---|
| `page_view` | `page_view` | `PageView` | Every route change in `_app.tsx` | `page_path` |
| `sign_up` | `sign_up` | `CompleteRegistration` | Register success callback | `method: "email"` |
| `begin_checkout` | `begin_checkout` | `InitiateCheckout` | Checkout page open | `order_id`, `value`, `currency: "VND"` |
| `purchase` | `purchase` | `Purchase` | Order status → `paid` confirmed | `transaction_id`, `value`, `currency: "VND"` |

---

## Helper Functions (src/components/analytics.tsx)

```ts
trackPageView(url: string)
trackSignUp(method?: string)
trackInitiateCheckout(orderId: string | number, value: number)
trackPurchase(orderId: string | number, amount: number)
```

---

## Integration Checklist

- [ ] `trackSignUp()` — call in register success handler
- [ ] `trackInitiateCheckout()` — call when checkout QR shown
- [ ] `trackPurchase()` — call in `order-status-poller.tsx` when status becomes `paid`
- [ ] `trackPageView()` — hook into `router.events` in `_app.tsx` (Phase 03)

---

## Env Vars Required

| Var | Description |
|---|---|
| `NEXT_PUBLIC_GA4_ID` | GA4 Measurement ID (G-XXXXXXXXXX) |
| `NEXT_PUBLIC_FB_PIXEL_ID` | Meta Pixel ID (numeric) |

---

## Consent Flow

```
User visits site
  → nsq_consent_v1 absent → show CookieConsent banner
  → User clicks "Chấp nhận tất cả"
    → setConsent({ analytics: true, marketing: true })
    → dispatch "nsq_consent_updated" event
    → Analytics component activates → injectGA4() + injectPixel()
  → User clicks "Từ chối"
    → setConsent({ analytics: false, marketing: false })
    → No scripts injected
```

---

*Last updated: 2026-05-26*
