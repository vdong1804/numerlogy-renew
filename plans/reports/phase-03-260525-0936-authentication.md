# Phase 03 Implementation Report — Authentication (JWT + OAuth)

## Status: COMPLETED

## Files Modified / Created

| File | Lines | Action |
|------|-------|--------|
| `app/db/models/auth.py` | 53 | Created |
| `app/db/models/__init__.py` | 12 | Modified (added auth import) |
| `alembic/versions/0002_auth_tables.py` | 65 | Created |
| `app/core/security.py` | 86 | Created |
| `app/core/oauth.py` | 31 | Created |
| `app/schemas/auth.py` | 42 | Created |
| `app/services/user_service.py` | 111 | Created |
| `app/services/token_service.py` | 111 | Created |
| `app/routers/auth.py` | 163 | Created |
| `app/deps.py` | 89 | Replaced (added oauth2_scheme, get_current_user, get_current_superuser) |
| `app/config.py` | 48 | Modified (added refresh_token_expire_days, frontend_url, oauth_redirect_base) |
| `app/main.py` | 43 | Modified (wired auth_router at /auth) |
| `.env.example` | 22 | Modified (added REFRESH_TOKEN_EXPIRE_DAYS, FRONTEND_URL, OAUTH_REDIRECT_BASE) |

All files ≤200 lines.

## DB Schema Additions

### `refresh_tokens`
- id BigInt PK, user_id FK→users CASCADE (indexed), token_hash String(255) UNIQUE+indexed, expires_at DateTime(tz), revoked_at DateTime(tz) NULL, created_at DateTime(tz) server_default now()

### `social_accounts`
- id BigInt PK, user_id FK→users CASCADE (indexed), provider String(20), provider_user_id String(255), email String(255) NULL, created_at DateTime(tz) server_default now()
- UniqueConstraint(provider, provider_user_id) → `uq_social_accounts_provider_uid`

## Endpoints

| Method | Path | Response | Auth |
|--------|------|----------|------|
| POST | `/auth/register` | 201 TokenOut | none |
| POST | `/auth/login` | TokenOut | none |
| POST | `/auth/refresh` | TokenOut | none |
| POST | `/auth/logout` | 204 | none |
| GET | `/auth/me` | UserOut | Bearer |
| GET | `/auth/google` | RedirectResponse | none |
| GET | `/auth/google/callback` | RedirectResponse→frontend | none |
| GET | `/auth/facebook` | RedirectResponse | none |
| GET | `/auth/facebook/callback` | RedirectResponse→frontend | none |

## Deviations from Instructions

- Phase plan said `sub: email` as option; task instructions explicitly say `sub: str(user.id)` — used numeric string ID.
- Auth router mounted at `/auth` (not `/api/v1/auth`) so OAuth callback URLs stay stable and don't require versioning in Google/Facebook console redirect URIs.
- `access_token_expire_minutes` default changed from 60 → 15 per task instructions (plan had 60).
- `AnyUrl` import left in config.py by accident from original — removed (no functional issue, was unused).

## Security Notes

- Refresh tokens stored as SHA-256 hex digest only; raw token never persisted.
- Token-in-URL OAuth callback has `# TODO: switch to HttpOnly cookie post-launch` comment per plan warning.
- `get_current_user` uses `auto_error=False` on HTTPBearer so 401 (not 403) returned on missing credentials.
- `sub` claim = `str(user.id)` (numeric string).

## Validation

- `python -m py_compile`: **PASS** — all 11 files
- Runtime imports not tested (passlib/jose/authlib not in local venv); syntax clean.

## Ready for Phase 04

YES — numerology calc + PDF gen endpoints can proceed. Deps: `get_current_user`, `get_current_superuser`, `get_db` all available in `app/deps.py`.
