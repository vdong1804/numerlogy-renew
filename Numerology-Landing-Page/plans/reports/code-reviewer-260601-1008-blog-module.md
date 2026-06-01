# Code Review — Blog tra cứu thần số học (numerology blog)

Date: 2026-06-01 | Reviewer: code-reviewer
Scope: src/modules/blog/*, src/pages/blog/*, src/pages/api/numerologyApi.ts, src/models/common.ts, src/modules/home/BlogNumerology.tsx
Build: next build PASSED, tsc 0 new errors. Findings below are runtime/logic/UX, not compile.

## Overall
Solid, consistent with existing theme/layout patterns. DOMPurify SSR pattern correct. Pagination has one real stale-state bug and a couple of edge cases. No critical security issues.

## CRITICAL
None.

## MAJOR

### M1 — Pagination "load more" can skip/duplicate items due to SWR cache + offset re-fetch race
File: src/modules/blog/BlogList.tsx:19-37, 96
The `onSuccess` appends `res.data` whenever a key resolves. SWR caches per key `['news-list', offset]`. On clicking "Xem thêm" → `setOffset(items.length)`. If the user navigates away and back, or `offset` key was previously cached, SWR may fire `onSuccess` again from cache **without** the user's intent, re-appending the same page → duplicates. Also if backend `total` shrinks between fetches, `hasMore` logic still fine, but duplicate-append risk remains.
Root issue: deriving accumulated state via `onSuccess` side-effect is fragile (onSuccess runs on every successful resolution incl. revalidation). `revalidateOnFocus:false` reduces but does not eliminate (revalidateIfStale, reconnect still active).
Fix: prefer `useSWRInfinite` (designed for this) OR guard append with a ref tracking which offsets already merged:
```ts
const merged = useRef<Set<number>>(new Set())
onSuccess: (res, key) => {
  const off = (key as any)[1] ?? offset
  if (merged.current.has(off)) return
  merged.current.add(off)
  setItems(prev => off === 0 ? res.data : [...prev, ...res.data])
}
```
Note: `onSuccess` second arg is the key — current code ignores it and reads `offset` from closure (see M2).

### M2 — Stale closure: onSuccess reads `offset` from closure, not the resolved key
File: src/modules/blog/BlogList.tsx:28-32
`offset === 0 ? res.data : [...]` reads `offset` from the render closure. SWR fetcher is also a closure over `offset`. In practice they align because changing `offset` re-renders, but if two fetches are in flight (rapid clicks, or initial + revalidation), the `onSuccess` for an older request can run with the newer `offset` value → wrong branch (replace vs append). Use the key arg as in M1 fix. Severity major because it silently corrupts the list.

## MINOR

### m1 — `disabled={isLoading}` on load-more is mostly inert
File: BlogList.tsx:95-106
After first page, `items.length>0`, so a subsequent fetch sets `isLoading` true only briefly; but because each offset is a new key, `isLoading` does reflect it — OK. However the `Loading` overlay (line 52) only shows when `items.length===0`, so "load more" gives no global spinner — button label handles it. Acceptable. Consider `isValidating` instead of `isLoading` for the button to reflect background revalidation. Low impact.

### m2 — Shared `getDetailNews` change also drives /post/[id] — verify backend
File: src/pages/api/numerologyApi.ts:58-62; consumer src/pages/post/[id].tsx:22
The path fix (`/api/new/{id}` → `/api/news/{id}`) and `.data.data` unwrap now also apply to the legacy Post page. PostContent.tsx renders 100% hardcoded content and only uses `postDetail?.title`, so the unwrap change is compatible (title still present). Good — but confirm /post/[id] is still a desired route or is now superseded by /blog/[id] (duplication, see m6).

### m3 — Detail page: no explicit "not found" for null data (only error)
File: BlogArticleDetail.tsx:48
`if (error) return <NotFound404/>`. If backend returns 200 with `{data:null}` (deleted/unknown id that doesn't 404), `data` is null, no error → renders empty article (blank title, no content, no image) instead of 404. Add: `if (!isLoading && data && !data.content && !data.title) ...` or treat `!data` after load as 404.

### m4 — `id` param not validated as numeric
File: BlogArticleDetail.tsx:20,24
`router.query.id` passed straight to API. Non-numeric `/blog/abc` will hit backend and likely 404 → NotFound404, acceptable. No fix required, just noted.

### m5 — Image fallback only on card, not on detail
File: BlogArticleDetail.tsx:43-46,89-96 vs BlogArticleCard.tsx:23,29-31
Card has FALLBACK_IMG; detail renders no image if `data.image` falsy (acceptable) but also no `onError` fallback if the URL 404s (broken-image icon shown). Card has same broken-URL risk (CardMedia shows nothing/broken). Minor: add `onError` handler to swap to FALLBACK_IMG. Matches existing code (BlogNumerologyCard has no fallback either) so consistent.

### m6 — Duplicate detail implementations: /post/[id] vs /blog/[id]
BlogNumerologyCard (home) still routes to `/post/${id}` (hardcoded article), while new BlogArticleCard routes to `/blog/${id}` (real content). Two detail experiences for the same News entity. Not a bug, but inconsistent UX. Recommend pointing home cards to `/blog/${id}` and retiring /post/[id] (or vice-versa) to avoid drift. Out of scope to rewrite — flag for product decision.

### m7 — XSS: sanitize config is default-allow; consider tightening
File: BlogArticleDetail.tsx:36
`DOMPurify.sanitize(data.content)` with defaults is safe against script/onerror (strips them) — pattern is SOUND. Default config DOES allow `target`/`href` etc. If content includes links, consider `ADD_ATTR:['target']` only if needed, and `{USE_PROFILES:{html:true}}` to be explicit. Current default is acceptable for trusted-ish admin CMS content. No action required unless content is user-generated.

### m8 — `Loading` overlay logic on list hides during load-more
File: BlogList.tsx:52 — `isOpen={isLoading && items.length===0}`. Intentional (avoid full-screen overlay on append). Good. No change.

## POSITIVE
- DOMPurify dynamic import in useEffect with `active` cleanup flag = correct SSR-safe pattern, no hydration/`window` issues. (BlogArticleDetail.tsx:29-41)
- SWR key `id ? ['news-detail', id] : null` correctly gates fetch until router ready. (line 22-25)
- `getDetailNews` path fix + `.data.data` unwrap matches documented backend contract `{data:News}`. Correct.
- `NewsListResponse` typed envelope matches `{data,total,limit,offset}`. Correct.
- Card fallback image, line-clamp, hover transitions — clean, theme-consistent.
- `coverImage`/`preview` memoization and BASE_URL prefixing consistent with BlogNumerologyCard.
- Empty-list ("Chưa có bài viết nào") and error-list states handled.

## Metrics
- New TS files: 0 new tsc errors (per task).
- Test coverage: none added (no tests in repo for modules observed).
- Lint: not run here; no obvious violations.

## Recommended actions (priority order)
1. Fix M1+M2 together: use SWR key arg in onSuccess + dedupe offsets (or migrate to useSWRInfinite). Prevents duplicate/corrupted list.
2. m3: treat post-load `!data`/empty as 404 in detail.
3. m6: align home cards + retire duplicate detail route (product decision).
4. m5/m7: optional hardening (img onError, explicit DOMPurify profile).

## Unresolved questions
1. Does backend `/api/news/{id}` return HTTP 404 for unknown id, or 200 with `{data:null}`? Determines whether m3 is required.
2. Is /post/[id] (hardcoded article) being deprecated in favor of /blog/[id]? Affects m6 and whether getDetailNews shape change has other consumers.
3. Is `content` (HTML) admin-authored/trusted, or could it ever be user-submitted? Affects m7 sanitize strictness.
4. Should "load more" preserve scroll/use infinite scroll, and is duplicate-fetch-on-back-navigation a real user flow to guard (M1)?
