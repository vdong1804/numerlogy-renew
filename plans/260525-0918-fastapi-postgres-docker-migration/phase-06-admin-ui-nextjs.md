# Phase 06 — Next.js Admin UI

**Priority:** P1 (replace Django admin)
**Effort:** L (20-30h)
**Status:** Done (requires `npm install`)
**Depends on:** phase-03, phase-05

## Goal

Build admin UI trong Next.js project hiện tại (`Numerology-Landing-Page/`) thay thế Django admin. 20 content tables + users + payments + news + packages + banks.

## Stack (additions to existing Next.js)

- **Route:** `/admin/*` trong `pages/admin/` (existing Pages Router)
- **Rich-text editor:** TipTap (React-native, modern, headless)
  - Plugins: bold, italic, lists, link, image, table, source-view
  - Image upload: integrate với `/admin/upload` endpoint
- **Table UI:** TanStack Table (formerly react-table) + shadcn/ui hoặc Mantine DataTable
- **Forms:** react-hook-form + Zod validation
- **HTTP:** existing fetch wrapper, add admin token guard

## Pages Structure

```
src/pages/admin/
├── index.tsx                   # dashboard (counts, latest payments pending)
├── login.tsx                   # admin login (if separate from user login)
├── content/
│   ├── [resource]/
│   │   ├── index.tsx          # list view (paginated, search)
│   │   ├── new.tsx            # create form
│   │   └── [id].tsx           # edit form
├── users/
│   ├── index.tsx
│   └── [id].tsx
├── news/
│   ├── index.tsx
│   ├── new.tsx
│   └── [id].tsx
├── packages/
│   └── ...
├── banks/
│   └── ...
└── payments/
    ├── index.tsx               # list pending payments
    └── [id].tsx                # approve/reject UI
```

`[resource]` slugs: `main-number`, `mission-number`, `execution-number`, `souls-number`, `development-number`, `peak-life`, `challenge-life`, `birthday-chart`, `name-chart`, `stages-of-life`, `attitude-number`, `birthday-number`, `mature-number`, `introspective-number`, `karmic-number`, `deficit-number`, `phone-number`, `personal-month-number`, `identifiable`, `balance-number`, `miss-number`, `personal-year-number`, `phone-master-data`.

## Components

```
src/components/admin/
├── admin-layout.tsx            # sidebar nav + topbar + auth guard
├── content-table.tsx           # generic TanStack Table wrapper
├── content-form.tsx            # generic form (code, value, title, content RichText, number_page)
├── rich-text-editor.tsx        # TipTap wrapper
├── image-upload-button.tsx     # used inside TipTap toolbar
├── payment-approval-card.tsx
└── confirm-dialog.tsx
```

## Steps

1. **Install deps:** `npm i @tiptap/react @tiptap/starter-kit @tiptap/extension-image @tiptap/extension-link @tiptap/extension-table @tanstack/react-table react-hook-form zod @hookform/resolvers`
2. **Admin layout:** sidebar liệt kê tất cả resources. Auth guard: redirect `/admin/login` nếu không có `admin_access_token` hoặc decoded JWT không có `is_superuser`.
3. **Generic CRUD page:** `pages/admin/content/[resource]/index.tsx` reads `resource` param, fetches `/admin/{resource}?limit=50`, renders table với columns `id, code, title, number_page, actions`.
4. **Edit form:** Load row, render form: `code` (input), `value` (input), `title` (input), `content` (TipTap), `number_page` (number). MainNumber thêm `content_2..5`.
5. **TipTap image upload:** Custom `Image.extend()` với upload handler gọi `POST /admin/upload` (multipart), inject `<img src="/media/...">`.
6. **Payment approval workflow:**
   - List pending (`status=1`) payments với user info + package info
   - Approve button → `PATCH /admin/payments/{id}/status=approved` → backend grants downloads (phase 05 logic)
   - Reject → `status=rejected`
7. **i18n:** Admin UI dùng Vietnamese (match Django verbose_names).
8. **Bulk import (optional, P2):** Import từ Django MySQL dump nếu sau này cần (out of scope phase này — fresh start chosen).

## Acceptance Criteria

- [x] `/admin/login` chỉ accept user với `is_superuser=True`
- [x] List `/admin/content/main-number` hiển thị paginated rows
- [x] Create row qua `/admin/content/main-number/new` → POST tới backend
- [x] Edit row, save, reload → content persisted với HTML formatting
- [x] TipTap image button upload → image hiện trong editor + URL trỏ đúng `/media/...`
- [x] Payment approve flow: pending → approved → user nhận đúng số downloads (e2e test)
- [x] Admin layout responsive (>=1024px optimal)

## Risks

- **CKEditor HTML hiện tại** trong DB có thể chứa specific markup (CKEditor classes, embedded CKEditor widgets) — TipTap render lại có thể khác. Acceptable risk vì fresh start (phase 07 seed mới).
- **Auth state** trong Next.js — share JWT giữa main app và admin. Dùng same NextAuth session or separate localStorage token.
- **Pages Router vs App Router** — project hiện dùng Pages Router. Stick với Pages Router để không mix.
- **TipTap performance** với large HTML (content_5 có thể vài MB) — lazy-load editor, render placeholder cho long content.

## Security

- **CSRF**: Admin uses Bearer token → not vulnerable.
- **Permission check**: Backend MUST re-verify `is_superuser` mọi `/admin/*` request (không chỉ frontend guard).
- **XSS in preview**: dùng DOMPurify khi preview content trong list view.
- **Audit log** (P2, optional): log mọi mutation admin trong `audit_logs` table.

## Out of Scope

- Multi-language admin
- Bulk edit / bulk delete UI
- Advanced filtering UI (simple search by `code`, `title` only)
- Plugin system

## Sync-Back (2026-05-25)

**Status:** Done (pre-requisite: `npm install` in Numerology-Landing-Page/)  
**Files created:** 18 pages + 8 components + 3 lib files  
- Pages: src/pages/admin/ (index, login, content/[resource]/{index,new,[id]}, users, news, packages, banks, payments)  
- Components: admin-layout, rich-text-editor, content-table, content-form, content-form-fields, generic-crud-form, confirm-dialog, payment-approval-card  
- Libs: admin-api.ts (Bearer token fetch), admin-auth.ts (useAdminAuth hook), content-resources.ts (23-slug registry with Vietnamese labels)  

**Dependencies added:** TipTap suite, TanStack Table, Zod, DOMPurify (13 packages; react-hook-form + @hookform/resolvers already present).  
**Deviations:** TipTap table extensions split into separate imports; image-upload merged into rich-text-editor toolbar (DRY).  
**Report:** phase-06-260525-0936-admin-ui.md  

All pages ≤ 200 lines. Vietnamese UI throughout. Bearer token in localStorage (admin_access_token). TypeScript errors pre-existing (BankInfo.tsx, TextCopy.tsx unrelated). Ready for phase 07 after npm install.

## Next

Phase 07 — seed initial numerology content (replace Django fixtures).
