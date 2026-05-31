# Unify User-Side Style with Home (Friendly + Smart)

**Goal:** Refactor non-home user pages to match the home page's design language — dark cosmic theme + warm orange + Philosopher headings + glass cards + decorative touches. Convey "friendly + smart".

## Home Design Tokens (source of truth)
- **Background:** `#031D2E` body, optional gradient `linear-gradient(180deg, #031D2E 0%, #0A2A40 100%)` + warm orange/violet radial halos
- **Text:** white `#fff`, secondary `rgba(255,255,255,0.7)`
- **Primary accent:** orange `#F96A2D`
- **Secondary accent:** violet `#6F49FD`
- **Fonts:** body `Raleway`, headings `Philosopher` (var `--philosopher-font`)
- **Buttons:** rounded-pill (9999px), contained orange, capitalized
- **Cards:** translucent `rgba(255,255,255,0.05-0.08)` + `border 1px solid rgba(255,255,255,0.12)` + `backdrop-filter: blur(10px)` + soft shadow
- **Section dividers:** subtle `#0E263B` / `#222F36`
- **Decorations:** subtle radial gradients, zodiac/satellite imagery accents
- **Animations:** spring fade-in, smooth hover

## Audit Summary
| Group | Pages | Current | Target |
|---|---|---|---|
| Already branded | login, register, forgot-password, reset-password | AuthShell dark+orange ✓ | Keep (minor Philosopher heading touch) |
| Legal/static | contact, privacy, terms, refund-policy | Plain HTML on dark bg, no theme | Wrap in `LegalShell` dark glass card |
| Help | faq, huong-dan | MUI white-ish, no Philosopher | Apply dark themed section + Philosopher heading + glass details |
| Account | my-account/* | Light `.account-shell` + orange | Add warm gradient bg + Philosopher headings + cosmic shimmer |
| Shop | shop/index, shop/[slug] | Tailwind light account-shell | Same: warm + Philosopher headings |
| Checkout | check-out/* | Light + Tailwind | Same: warm + Philosopher headings |
| Result | ket-qua, post | MUI on dark | Verify Philosopher consistency |
| 404 | 404 | Component | Check, polish if needed |

## Phases
1. **Phase 1: Create reusable wrappers + shared styles**
   - `LegalShell` component (dark glass card for static pages)
   - `PageHeading` component (Philosopher font + orange underline)
   - Extend `admin.css` `.account-shell` with: cosmic gradient bg, Philosopher headings via `.account-shell h1/h2`, warmer card hover
2. **Phase 2: Legal pages refactor** (contact, privacy, terms, refund-policy)
3. **Phase 3: Help pages refactor** (faq, huong-dan)
4. **Phase 4: Account pages polish** (subtle, keep existing structure; add Philosopher headings + warm hero)
5. **Phase 5: Shop + Checkout polish**
6. **Phase 6: Review + typecheck**

## Risk
- Tailwind preflight is OFF; light/dark token system in `account-shell` must not break
- Auth pages already use dark theme — minimal touches only
- Keep `account-shell` light (a previous design decision); just add warmth + Philosopher
