"""Auth router: JWT register/login/refresh/logout/me + forgot/reset password."""

import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import verify_password
from app.db.session import async_session_factory
from app.deps import get_current_user, get_db
from app.middleware.rate_limit import limiter
from app.services import email_outbox_service, fulfillment_service
from app.services import turnstile_service

logger = logging.getLogger(__name__)
from app.schemas.auth import (
    ForgotPasswordIn,
    LoginIn,
    RefreshIn,
    RegisterIn,
    ResetPasswordIn,
    TokenOut,
    UserOut,
)
from app.services.email_service import send_password_reset_email
from app.services.password_reset_service import (
    consume_reset_token,
    create_reset_token,
    revoke_all_user_refresh_tokens,
)
from app.services.token_service import issue_token_pair, revoke_refresh, rotate_refresh
from app.services.user_service import (
    create_user,
    get_user_by_email,
    get_user_by_id,
    update_user_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])


async def _grant_lead_magnet_bg(user_id: int, profile_name: str) -> None:
    """Background task: render free report after register. Best-effort."""
    try:
        async with async_session_factory() as bg_db:
            await fulfillment_service.grant_lead_magnet(bg_db, user_id, profile_name)
            await bg_db.commit()
    except Exception:  # noqa: BLE001
        logger.exception("Lead magnet grant failed for user %s", user_id)


@router.post("/register", response_model=TokenOut, status_code=status.HTTP_201_CREATED)
@limiter.limit("3/minute")
async def register(
    request: Request,
    body: RegisterIn,
    bg: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> TokenOut:
    """Create a new user account and return tokens (auto-login).

    Rate-limited to 3/minute per IP. Validates Turnstile CAPTCHA token.
    Schedules a background job to render the free lead-magnet report so the
    HTTP response is not blocked by wkhtmltopdf.
    """
    # Verify Turnstile CAPTCHA — skipped transparently when secret key not set (dev)
    if not await turnstile_service.verify(body.captcha_token, request.client.host if request.client else None):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Captcha failed")

    existing = await get_user_by_email(db, body.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email already registered"
        )
    user = await create_user(db, body.email, body.password, body.first_name, body.last_name)
    bg.add_task(
        _grant_lead_magnet_bg,
        user.id,
        f"{body.first_name} {body.last_name}".strip() or body.email,
    )
    # Welcome email (best-effort)
    try:
        await email_outbox_service.enqueue(
            db,
            to_email=user.email,
            template="welcome",
            payload={"name": f"{body.first_name} {body.last_name}".strip()},
            user_id=user.id,
        )
    except Exception:  # noqa: BLE001
        logger.exception("Welcome email enqueue failed for %s", user.email)
    return await issue_token_pair(db, user.id)


@router.post("/login", response_model=TokenOut)
@limiter.limit("5/minute")
async def login(request: Request, body: LoginIn, db: AsyncSession = Depends(get_db)) -> TokenOut:
    """Authenticate with email + password; return access + refresh tokens.

    Rate-limited to 5/minute per IP to slow brute-force.
    """
    user = await get_user_by_email(db, body.email)
    if not user or not user.hashed_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )
    if not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Account disabled"
        )
    return await issue_token_pair(db, user.id)


@router.post("/refresh", response_model=TokenOut)
async def refresh(body: RefreshIn, db: AsyncSession = Depends(get_db)) -> TokenOut:
    """Rotate refresh token: revoke old, issue new access + refresh pair."""
    try:
        return await rotate_refresh(db, body.refresh_token)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(body: RefreshIn, db: AsyncSession = Depends(get_db)) -> None:
    """Revoke refresh token (blocklist). Idempotent."""
    await revoke_refresh(db, body.refresh_token)


@router.get("/me", response_model=UserOut)
async def me(current_user=Depends(get_current_user)) -> UserOut:
    """Return authenticated user's profile."""
    return UserOut.model_validate(current_user)


async def _forgot_password_key(request: Request) -> str:
    """Rate-limit key = IP + email parsed from JSON body.

    slowapi evaluates key_func BEFORE the handler body runs, so request.state
    fields set inside the handler are not yet available here. We parse the body
    directly instead. The body is cached by Starlette so reading it twice is safe.
    """
    ip = (
        request.headers.get("CF-Connecting-IP")
        or (request.client.host if request.client else "unknown")
    )
    try:
        data = await request.json()
        email = data.get("email", "unknown") if isinstance(data, dict) else "unknown"
    except Exception:  # noqa: BLE001 — malformed JSON or body already consumed
        email = "unknown"
    return f"{ip}:{email}"


@router.post("/forgot-password", status_code=status.HTTP_202_ACCEPTED)
@limiter.limit("3/minute", key_func=_forgot_password_key)
async def forgot_password(
    request: Request,
    body: ForgotPasswordIn,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Issue a password-reset token and email it to the user.

    Rate-limited 3/minute per IP+email. Always returns 202 to prevent email enumeration.
    Validates Turnstile CAPTCHA token.
    """
    # Verify Turnstile CAPTCHA — skipped transparently when secret key not set (dev)
    if not await turnstile_service.verify(body.captcha_token, request.client.host if request.client else None):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Captcha failed")

    user = await get_user_by_email(db, body.email)
    if user and user.is_active:
        raw_token = await create_reset_token(db, user.id)
        # Email send is best-effort; failure must not reveal account presence
        try:
            send_password_reset_email(user.email, raw_token)
        except Exception:  # pragma: no cover - logged inside service
            pass
    return {"detail": "If the email exists, a reset link has been sent."}


@router.post("/reset-password", status_code=status.HTTP_204_NO_CONTENT)
async def reset_password(
    body: ResetPasswordIn, db: AsyncSession = Depends(get_db)
) -> None:
    """Consume reset token, update password, revoke active refresh tokens."""
    try:
        user_id = await consume_reset_token(db, body.token)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    user = await get_user_by_id(db, user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User not eligible")

    await update_user_password(db, user, body.new_password)
    await revoke_all_user_refresh_tokens(db, user.id)
