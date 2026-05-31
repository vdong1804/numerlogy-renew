# Phase 02 — Frontend Auth Refactor (Remove SNS, Add Pages)

## Overview
- **Priority:** High
- **Status:** pending
- **Depends on:** Phase 01 (backend endpoints)

Strip `next-auth` + SNS UI. Add `/login`, `/register`, `/forgot-password`, `/reset-password` pages. Store JWT in cookies (`js-cookie`). Provide a thin `useUserAuth` hook for header & protected routes.

## Files to Modify
- `Numerology-Landing-Page/src/pages/_app.tsx` — drop `SessionProvider`
- `Numerology-Landing-Page/src/layouts/Header.tsx` — replace `useSession`/`signIn`/`signOut` with cookie-based auth; replace `ModalLoginSocial` with router push to `/login`
- `Numerology-Landing-Page/src/layouts/Main.tsx` — drop `useSession` + `convertTokenSocial` effect
- `Numerology-Landing-Page/src/pages/api/axiosClient.ts` — set `BASE_URL` default `NEXT_PUBLIC_API_BASE`; restore Bearer token interceptor from cookies
- `Numerology-Landing-Page/src/pages/api/numerologyApi.ts` — remove `convertTokenSocial` + SNS constants imports
- `Numerology-Landing-Page/src/utils/constant.ts` — drop SNS constants
- `Numerology-Landing-Page/src/models/common.ts` — drop `SocialLoginType` + `ConvertTokenOutput`
- `Numerology-Landing-Page/package.json` — drop `next-auth` dependency

## Files to Create
- `Numerology-Landing-Page/src/lib/user-auth.ts` — token cookie helpers (`setUserTokens`, `clearUserTokens`, `getAccessToken`) + `useUserAuth` hook (fetches `/auth/me`)
- `Numerology-Landing-Page/src/lib/user-api.ts` — fetch wrapper with bearer + 401 redirect to `/login`
- `Numerology-Landing-Page/src/pages/login.tsx` — email/password form, on success store tokens + redirect to `/`
- `Numerology-Landing-Page/src/pages/register.tsx` — email/first_name/last_name/password form
- `Numerology-Landing-Page/src/pages/forgot-password.tsx` — email input, calls `/auth/forgot-password`, shows confirmation
- `Numerology-Landing-Page/src/pages/reset-password.tsx` — reads `?token=` query, new password + confirm, calls `/auth/reset-password`

## Files to Delete
- `Numerology-Landing-Page/src/pages/api/auth/[...nextauth].ts`
- `Numerology-Landing-Page/src/pages/api/restricted.ts`
- `Numerology-Landing-Page/src/components/modal/ModalLoginSocial.tsx`
- `Numerology-Landing-Page/src/components/button/ButtonSocialSignIn.tsx`
- `Numerology-Landing-Page/src/components/icon/IconFacebookLogin.tsx`
- `Numerology-Landing-Page/src/components/icon/IconTwitterLogin.tsx`
- `Numerology-Landing-Page/src/types/next-auth-d.ts`

## Implementation Steps

1. **Cookie helpers (`lib/user-auth.ts`)**
   - `ACCESS_KEY = 'access_token'`, `REFRESH_KEY = 'refresh_token'` (matches existing Cookies.remove calls)
   - `setUserTokens({access, refresh})`, `clearUserTokens()`, `getAccessToken()`
   - `useUserAuth()` hook — pulls token, calls `/auth/me`, returns `{ user, loading, logout }`

2. **API wrapper (`lib/user-api.ts`)**
   - Wraps fetch with bearer + JSON; routes 401 to `/login`
   - Helpers: `postJson`, `getJson`

3. **Login page (`pages/login.tsx`)**
   - react-hook-form, MUI styled card matching site theme
   - On submit → `POST /auth/login` → setUserTokens → redirect (callback url or `/`)
   - Link to `/register` and `/forgot-password`
   - Vietnamese labels

4. **Register page (`pages/register.tsx`)**
   - Fields: email, first_name, last_name, password, confirm_password
   - `POST /auth/register` → setUserTokens → redirect to `/`

5. **Forgot password (`pages/forgot-password.tsx`)**
   - Email field; on submit `POST /auth/forgot-password`
   - Always show success "Email đã được gửi nếu địa chỉ tồn tại"

6. **Reset password (`pages/reset-password.tsx`)**
   - `useRouter` to read `token` query
   - new_password + confirm fields → `POST /auth/reset-password`
   - On success redirect to `/login`

7. **Header refactor**
   - `useUserAuth()` instead of `useSession`
   - Button "Đăng Nhập" → `router.push('/login')`
   - Menu items: profile, logout (clearUserTokens + redirect)
   - Remove `ModalLoginSocial`

8. **_app.tsx:** drop `SessionProvider`

9. **Main.tsx:** drop useSession + convertTokenFunc effect

10. **axiosClient.ts:** uncomment cookie interceptor (use `js-cookie`); use `NEXT_PUBLIC_API_BASE`

11. **Cleanup:** delete SNS files; drop `next-auth` from package.json (manual edit, no `npm install`)

12. **Build check:** `npm run check-types`

## Todo
- [ ] user-auth.ts + user-api.ts
- [ ] login.tsx
- [ ] register.tsx
- [ ] forgot-password.tsx
- [ ] reset-password.tsx
- [ ] Header refactor
- [ ] _app.tsx + Main.tsx
- [ ] axiosClient.ts + numerologyApi.ts cleanup
- [ ] delete SNS files
- [ ] package.json (drop next-auth)
- [ ] check-types

## Success Criteria
- No `next-auth` import remains
- `/login`, `/register`, `/forgot-password`, `/reset-password` routes work
- Header shows login button when logged out, user menu when logged in
- TypeScript compiles (`check-types`)

## Risks
- `axiosClient.ts` interceptor was commented out — re-enabling may affect existing endpoints (numerology free endpoints don't need auth, so should be safe)
- `js-cookie` types already installed
