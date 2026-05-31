# Legal Content Sources

Tracks template versions and last-updated dates for all legal pages.
All content drafted in Vietnamese per NĐ 13/2023 and applicable VN consumer law.

---

## Pages

| Page | File | Version | Last Updated | Content Source |
|---|---|---|---|---|
| Điều khoản sử dụng | `src/pages/terms.tsx` | 1.0 | 2026-05-26 | Internal template — jurisdiction TP HCM |
| Chính sách bảo mật | `src/pages/privacy.tsx` | 1.0 | 2026-05-26 | NĐ 13/2023/NĐ-CP template |
| Chính sách hoàn tiền | `src/pages/refund-policy.tsx` | 1.0 | 2026-05-26 | Internal — digital goods policy |
| Liên hệ | `src/pages/contact.tsx` | 1.0 | 2026-05-26 | Internal |

---

## Placeholder Index

All `[BRACKETS]` placeholders require user fill-in before launch:

| Placeholder | Location | Description |
|---|---|---|
| `[TÊN DOANH NGHIỆP]` | terms, privacy, contact | Legal entity name |
| `[MST]` | terms, privacy, contact | Mã số thuế |
| `[MST / SỐ GPKD]` | contact | MST hoặc số GPKD |
| `[ĐỊA CHỈ ĐẦY ĐỦ]` | terms, privacy, contact | Registered address |
| `[EMAIL HỖ TRỢ]` | terms, privacy, refund, contact | Support email |
| `[EMAIL DPO]` | privacy | Data Protection Officer email |
| `[TÊN DPO]` | privacy | DPO name |
| `[SỐ ĐIỆN THOẠI]` | contact | Hotline |
| `[ZALO OA LINK]` | refund, contact | Zalo Official Account URL |

---

## Legal Review Status

- [ ] Luật sư review terms.tsx — recommended before launch
- [ ] Luật sư review privacy.tsx — recommended (NĐ 13 compliance)
- [ ] Luật sư review refund-policy.tsx — recommended
- [x] Placeholder audit complete — all [BRACKETS] documented above

---

## Update Protocol

When updating legal content:
1. Bump `version` in this doc and in the page's "Cập nhật lần cuối" line
2. Note what changed and why
3. If material change (new data processing, new third party): re-notify users via email or consent re-prompt

---

*Last updated: 2026-05-26*
