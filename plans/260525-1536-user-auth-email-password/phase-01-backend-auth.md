# Phase 01 — Backend Auth Refactor (Remove SNS, Add Forgot/Reset)

## Overview
- **Priority:** High
- **Status:** pending

Remove Google/Facebook OAuth from FastAPI. Add forgot/reset password flow with email link. Drop `social_accounts` table; add `password_reset_tokens` table.

## Files to Modify
- `numerology-api/app/routers/auth.py` — strip OAuth routes, add forgot/reset
- `numerology-api/app/schemas/auth.py` — add `ForgotPasswordIn`, `ResetPasswordIn`
- `numerology-api/app/services/user_service.py` — drop `get_or_create_social_user`
- `numerology-api/app/services/token_service.py` — keep as-is
- `numerology-api/app/db/models/auth.py` — remove `SocialAccount`, add `PasswordResetToken`
- `numerology-api/app/config.py` — drop google/facebook keys, add SMTP + reset settings
- `numerology-api/app/main.py` — no change (oauth not in middleware)

## Files to Create
- `numerology-api/app/services/password_reset_service.py` — issue/validate/consume reset tokens
- `numerology-api/app/services/email_service.py` — minimal SMTP sender, log fallback
- `numerology-api/alembic/versions/0003_drop_social_add_reset.py` — schema change

## Files to Delete
- `numerology-api/app/core/oauth.py` — Authlib config no longer needed

## Implementation Steps

1. **Schemas (`schemas/auth.py`)**
   - Add `ForgotPasswordIn(email: EmailStr)`
   - Add `ResetPasswordIn(token: str, new_password: str)` with min length 8 validator

2. **Model (`db/models/auth.py`)**
   - Remove `SocialAccount` class + export
   - Add `PasswordResetToken`: `id`, `user_id` FK, `token_hash` (SHA-256, unique), `expires_at`, `used_at` (nullable), `created_at`

3. **Service `password_reset_service.py`**
   - `create_reset_token(db, user_id) -> raw_token` (random 32 bytes hex, hash stored, exp 30min)
   - `consume_reset_token(db, raw_token) -> user_id` (validate not expired/used, mark used)

4. **Service `email_service.py`**
   - `send_password_reset_email(to_email, reset_url)` — use `smtplib.SMTP_SSL` if settings present, else log
   - Read SMTP config from `settings`

5. **Config (`config.py`)**
   - Remove: `google_client_id`, `google_client_secret`, `facebook_app_id`, `facebook_app_secret`, `oauth_redirect_base`
   - Add: `smtp_host`, `smtp_port`, `smtp_user`, `smtp_password`, `smtp_from`, `password_reset_token_expire_minutes` (default 30), `password_reset_url_base` (frontend URL pattern)

6. **Router (`routers/auth.py`)**
   - Delete Google/Facebook routes & imports (oauth, get_or_create_social_user)
   - Add `POST /auth/forgot-password` → lookup user; if exists issue token + send email; **always return 202** to avoid email enumeration
   - Add `POST /auth/reset-password` → consume token, update password hash, revoke all user's refresh tokens

7. **User service (`user_service.py`)**
   - Remove `get_or_create_social_user`
   - Remove `SocialAccount` import

8. **Delete `core/oauth.py`**

9. **Migration `0003_drop_social_add_reset.py`**
   - `op.drop_table("social_accounts")` (also drop indexes/unique)
   - `op.create_table("password_reset_tokens", ...)` with same shape as model

10. **Compile check:** `python -c "from app.main import app"` from numerology-api

## Todo
- [ ] schemas
- [ ] model
- [ ] services (reset + email)
- [ ] config
- [ ] router refactor
- [ ] user_service cleanup
- [ ] delete oauth.py
- [ ] migration
- [ ] compile-check

## Success Criteria
- `/auth/google*` and `/auth/facebook*` return 404
- `/auth/forgot-password` returns 202 (idempotent on unknown email)
- `/auth/reset-password` updates password and invalidates refresh tokens
- Alembic `upgrade head` clean

## Security
- Token: 32-byte secure random, SHA-256 hashed in DB
- One-time use (`used_at` set on consume)
- 30-min expiry
- Reset revokes all refresh tokens (force re-login)
- No email enumeration (always 202)
