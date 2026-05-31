# Lint Cleanup Backlog

**Status:** Deferred to Phase 04
**Blocking:** `ignoreBuildErrors: true` + `ignoreDuringBuilds: true` in `Numerology-Landing-Page/next.config.js`

---

## Context

Phase 03 frontend agent identified 100+ pre-existing lint / TypeScript errors concentrated in
`src/components/admin/*`. The ignore flags were retained to keep the build green.
Remove both flags only after all items below are resolved.

---

## Known Issues

### 1. Prettier formatting violations
- **Scope:** `src/components/admin/**/*.tsx`
- **Action:** Run `npx prettier --write src/components/admin/` and commit.

### 2. Import sort order (eslint-plugin-import / simple-import-sort)
- **Scope:** Various files in `src/components/admin/`
- **Action:** Run `npx eslint --fix src/components/admin/` or configure auto-fix in CI.

### 3. `no-nested-ternary` violations
- **Scope:** Multiple files in `src/components/admin/`
- **Action:** Refactor nested ternaries into explicit `if` blocks or named variables.

### 4. TypeScript generics / `window` casts in Phase 03 surface
- **Scope:** `src/components/turnstile-widget.tsx` — `window` casts use `Record<string, unknown>`
  which is acceptable but worth reviewing against stricter typings post-launch.
- **Action:** Low priority; audit after admin errors are cleared.

---

## Recommended Phase 04 Steps

1. Fix Prettier + import-sort in admin components (autofix, low risk).
2. Manually refactor `no-nested-ternary` violations.
3. Remove `ignoreDuringBuilds: true` from `next.config.js` `eslint` block.
4. Remove `ignoreBuildErrors: true` from `next.config.js` `typescript` block.
5. Run `npm run build` and fix any newly surfaced errors.
6. Update this file to mark resolved.
