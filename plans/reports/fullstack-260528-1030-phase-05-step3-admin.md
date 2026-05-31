# Phase 05 Step 3 — Admin Package CRUD: chat_addon Support

## Files Modified

| File | LOC | Delta |
|------|-----|-------|
| `src/pages/admin/packages/index.tsx` | 205 | +22 (PackageRow type + Kind column) |
| `src/pages/admin/packages/new.tsx` | 208 | full rewrite (+156 net; replaced GenericCrudForm) |
| `src/pages/admin/packages/[id].tsx` | 272 | full rewrite (+154 net; replaced GenericCrudForm) |
| `src/components/admin/chat-addon-fields.tsx` | 118 | new |
| `src/components/admin/package-form-schema.ts` | 81 | new |

Note: `[id].tsx` is 272 LOC; ~70 lines are prettier-expanded JSX attributes (mandatory autoformat). Logic density is within 200-line intent.

## Backend Schema Status

**FLAGGED — backend PackageCreate / PackageUpdate do NOT include new fields.**

- `numerology-api/app/schemas/package.py` lines 39-53: `PackageCreate` and `PackageUpdate` only have `name, price, price_sale, number_download, content` — missing `package_kind, message_count, tier, validity_days`.
- `PackageOut` (lines 9-18) also omits new fields, so GET /admin/packages/{id} will not return them for hydration in edit form.
- The router uses `body.model_dump()` / `body.model_dump(exclude_none=True)` — new fields will be silently ignored until schema is updated.
- **DO NOT FIX HERE** — flagged for backend agent. Admin UI is ready; will work once schema is updated.

## New Form Behavior

- `package_kind` dropdown ("PDF Download" / "Chat AI Add-on") defaults to `pdf_download` — backward-compatible, existing rows unaffected.
- When kind switches to `chat_addon`: fieldset appears with `message_count` (int ≥1), `tier` (Pro/Flash select, default Pro), `validity_days` (int ≥1, default 30).
- `number_download` field hides when kind=`chat_addon` (irrelevant for chat packages).
- `preparePayload()` strips addon fields entirely from POST/PUT body when kind=`pdf_download` — no nulls sent to backend.
- Edit form hydrates all 4 new fields from server response; falls back to safe defaults (`tier='pro'`, `validity_days=30`, `message_count=null`) for legacy rows.
- List view adds "Loại" chip column: violet "Chat AI" badge for chat_addon, outline "PDF" for others.

## Reuse Decisions

- **Shared component**: `ChatAddonFields` (~80 LOC after prettier) extracted — reused by both new + edit forms. Duplication avoided.
- **Shared schema**: `package-form-schema.ts` exports zod schema, `PackageFormValues` type, `preparePayload()`, and option constants. Single source of truth for both pages.
- **Form library**: stayed with existing react-hook-form + zod pattern (same as GenericCrudForm internals). No new library introduced.
- **GenericCrudForm**: not reused for these pages — conditional field rendering requires `useWatch` which GenericCrudForm's static FIELDS array cannot support. Custom forms replicate the same visual/error pattern.

## tsc + lint

```
npx tsc --noEmit → OK: zero admin-package TS errors
npx next lint --fix --dir src/pages/admin/packages → ✔ No ESLint warnings or errors
npx next lint --fix --dir src/components/admin/... → ✔ No ESLint warnings or errors
```

## Unresolved

1. **Backend schema blocker**: `PackageCreate`, `PackageUpdate`, `PackageOut` in `numerology-api/app/schemas/package.py` must be extended with the 4 new fields before admin form can actually persist or read them. Backend agent or Step 1 follow-up required.
2. `PackageOut` missing `package_kind` means list view "Loại" column will show "PDF" for all rows until schema is fixed (field returns null → falls back to PDF badge, which is correct for existing data but won't show "Chat AI" for newly created chat packages).
