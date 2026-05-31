# User Site Auth: Remove SNS + Add Email/Password Auth

**Created:** 2026-05-25
**Scope:** Backend (FastAPI) + Frontend (Numerology-Landing-Page)
**Mode:** Single PR (decoupled phases)

## Goal
Loại bỏ hoàn toàn đăng nhập SNS (Google/Facebook/Twitter). Thêm flow đăng nhập / đăng ký / quên mật khẩu cho user site bằng email + password.

## Decisions
- **Forgot password:** Email link token (đầy đủ) — backend tạo bảng `password_reset_tokens` + endpoints `/auth/forgot-password` & `/auth/reset-password`. Email gửi qua SMTP, fallback log nếu SMTP chưa cấu hình.
- **Token storage:** Cookies (js-cookie) ở user site.
- **SNS removal:** Xoá toàn bộ frontend + backend, kèm migration drop bảng `social_accounts`.

## Phases

| # | File | Status |
|---|------|--------|
| 01 | [phase-01-backend-auth.md](./phase-01-backend-auth.md) | pending |
| 02 | [phase-02-frontend-auth.md](./phase-02-frontend-auth.md) | pending |
| 03 | [phase-03-test-docs.md](./phase-03-test-docs.md) | pending |

## Key Dependencies
- Backend changes ship first (frontend depends on new endpoints).
- Migration `0003_drop_social_remove_oauth.py` + add `password_reset_tokens` must run before user flow tested.
- Frontend removes `next-auth` package; cookies replace SessionProvider.
