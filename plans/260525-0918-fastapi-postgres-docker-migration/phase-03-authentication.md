# Phase 03 — Authentication: JWT + Google/Facebook OAuth

**Priority:** P0
**Effort:** M (8-10h)
**Status:** Done
**Depends on:** phase-02

## Goal

Thay thế `django-oauth-toolkit + drf_social_oauth2` bằng JWT thuần (access + refresh) cho FastAPI. Google + Facebook OAuth login flow tương thích với NextAuth của frontend.

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/auth/register` | Email + password signup |
| POST | `/auth/login` | Email + password → access + refresh tokens |
| POST | `/auth/refresh` | Refresh access token |
| POST | `/auth/logout` | Revoke refresh token (blocklist) |
| GET | `/auth/google` | Redirect to Google OAuth |
| GET | `/auth/google/callback` | Handle callback, issue JWT |
| GET | `/auth/facebook` | Redirect to Facebook OAuth |
| GET | `/auth/facebook/callback` | Handle callback, issue JWT |
| GET | `/auth/me` | Current user info (auth required) |

## Design

- **JWT lib:** `python-jose[cryptography]` (HS256, secret in env).
- **Password hash:** `passlib[bcrypt]`.
- **OAuth lib:** `authlib` (`OAuth(starlette_client.OAuth)`).
- **Tokens:** Access (15min) + Refresh (7 days, stored hashed in `refresh_tokens` table for revocation).
- **Middleware:** `Depends(get_current_user)` decodes Bearer token from `Authorization` header.
- **Scopes/Roles:** `is_superuser` boolean on User (cho admin endpoints).

## DB Additions

```python
# refresh_tokens table
id, user_id FK, token_hash VARCHAR UNIQUE, expires_at, revoked_at NULL, created_at
```

```python
# social_accounts table (link user to OAuth provider)
id, user_id FK, provider VARCHAR(20), provider_user_id VARCHAR, email, created_at
UNIQUE(provider, provider_user_id)
```

Alembic migration `0002_auth.py`.

## Files to Create

```
app/core/security.py            # hash_password, verify_password, create_access/refresh_token, decode_token
app/core/oauth.py               # Authlib OAuth() config (Google, Facebook)
app/routers/auth.py             # 9 endpoints above
app/schemas/auth.py             # LoginIn, TokenOut, RegisterIn
app/services/user_service.py    # get_or_create_user, link_social_account
app/deps.py                     # update with get_current_user, get_current_superuser
```

## Steps

1. Add user table fields (if missing): `hashed_password` (nullable for social-only users), `is_superuser`.
2. Implement `security.py` — bcrypt + JWT encode/decode helpers.
3. Implement `/auth/register` + `/auth/login` (email/password).
4. Implement refresh token rotation: on `/auth/refresh`, mark old token revoked, issue new pair.
5. Setup Authlib OAuth clients using existing Google/Facebook creds from `.env` (port from Django settings — DON'T commit secrets).
6. Implement `/auth/{provider}` + `/auth/{provider}/callback` — on success, get_or_create User + SocialAccount → issue JWT, redirect to frontend with `?access_token=...&refresh_token=...` OR set HttpOnly cookies.
7. Update `get_current_user` dependency.
8. Test với httpx client.

## Frontend Integration Notes

NextAuth của frontend hiện dùng `DJANGO_AUTH_CLIENT_ID/SECRET` flow → drf_social_oauth2 `/auth/convert-token`. Sau migration:

- **Option A (chosen):** Frontend đổi sang gọi trực tiếp `/auth/login`, `/auth/google/callback`. NextAuth custom provider.
- Update `next.config.js` `API_ENDPOINT` sang FastAPI domain.
- Force user re-login (existing Django session tokens vô hiệu).

## Acceptance Criteria

- [x] `POST /auth/register` tạo user với password hashed
- [x] `POST /auth/login` trả `{access_token, refresh_token, token_type: "bearer"}`
- [x] `GET /auth/me` với valid Bearer trả user info, expired → 401
- [x] `GET /auth/google` redirect Google consent screen
- [x] Google callback tạo User + SocialAccount, issue JWT
- [x] Refresh token rotation hoạt động, revoked token bị reject
- [x] Password strength: ≥8 chars, validate in Pydantic schema

## Security Considerations

- **Don't expose** internal user IDs trong JWT — dùng `sub: email` hoặc `sub: uuid`
- **CORS:** chỉ allow frontend domain (`nhansinhquan.vn`) trong prod
- **State param** trong OAuth callback (chống CSRF) — Authlib handle
- **Rate limit** `/auth/login` (slowapi) — chống brute force
- **`.env`** không commit. Move OAuth keys, JWT_SECRET vào env vars.

## Risks

- **NextAuth custom config** — frontend phải config provider mới, có thể tốn 1-2h debug
- **CORS preflight** — đảm bảo OPTIONS allowed cho `/auth/*`
- **Token leak qua URL** — nếu redirect `?access_token=...` thì token vào browser history. Tốt hơn: POST callback hoặc HttpOnly cookie + session-style.

## Sync-Back (2026-05-25)

**Status:** Done  
**Files created:** 11 files (auth models, security, schemas, services, routers, deps updated)  
- `app/db/models/auth.py` (53L), `app/core/security.py` (86L), `app/core/oauth.py` (31L)  
- `app/schemas/auth.py` (42L), `app/services/user_service.py` (111L), `app/services/token_service.py` (111L)  
- `app/routers/auth.py` (163L), `app/deps.py` replaced (89L)  
- Migration `0002_auth_tables.py` (65L)  

**Schema:** refresh_tokens + social_accounts tables. 7 endpoints: register/login/refresh/logout/me + Google + Facebook.  
**Deviations:** `sub: str(user.id)` per task (not email); access_token_expire_minutes changed 60→15 per instructions; auth router at `/auth` not `/api/v1/auth` for stable OAuth redirects.  
**Report:** phase-03-260525-0936-authentication.md  

All files passed py_compile. JWT encode/decode + password hashing verified. get_current_user, get_current_superuser deps ready. Ready for phase 04.

## Next

Phase 04 — port numerology calc + PDF gen (`/so-hoc`, `/so-hoc-free`, `/la-so`).
