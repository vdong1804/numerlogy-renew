"""Profile router — GET/PUT /api/profile + DSAR DELETE /api/profile/chat-data."""

import logging

from fastapi import APIRouter, Depends
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_current_user, get_db
from app.db.models.user import User, UserProfile
from app.schemas.profile import UserWithProfileOut, ProfileNestedOut, ProfileUpdate

logger = logging.getLogger(__name__)

profile_router = APIRouter(prefix="/api", tags=["profile"])


@profile_router.get("/profile", response_model=dict)
async def get_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return user + profile. Auto-creates profile if missing."""
    result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()

    if profile is None:
        name = f"{current_user.first_name} {current_user.last_name}".strip()
        profile = UserProfile(user_id=current_user.id, name=name, number_download=0)
        db.add(profile)
        await db.flush()
        await db.refresh(profile)

    profile_data = ProfileNestedOut.model_validate(profile)
    out = UserWithProfileOut(
        id=current_user.id,
        email=current_user.email,
        profile=profile_data,
    )
    return {"data": out.model_dump()}


@profile_router.put("/profile", response_model=dict)
async def update_profile(
    body: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update profile fields (partial)."""
    result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()

    if profile is None:
        name = body.name or f"{current_user.first_name} {current_user.last_name}".strip()
        profile = UserProfile(user_id=current_user.id, name=name, number_download=0)
        db.add(profile)

    for field, value in body.model_dump(exclude_none=True).items():
        setattr(profile, field, value)

    await db.flush()
    await db.refresh(profile)
    profile_data = ProfileNestedOut.model_validate(profile)
    out = UserWithProfileOut(id=current_user.id, email=current_user.email, profile=profile_data)
    return {"data": out.model_dump()}


@profile_router.delete("/profile/chat-data", response_model=dict)
async def delete_chat_data(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """DSAR endpoint — purge user's chat history + PDF index + abuse flags.

    Billing-relevant rows (chat_addon_purchases) keep the row but anonymize
    user_id NULL so accounting stays intact. Cascade FKs on conversations /
    messages / user_pdf_index handle the dependent rows. Idempotent —
    calling twice is safe (rowcounts may be zero on the second call).
    """
    user_id = current_user.id
    # CASCADE removes chat_messages via FK on conversations.
    conv_res = await db.execute(
        text("DELETE FROM chat_conversations WHERE user_id = :u"),
        {"u": user_id},
    )
    pdf_res = await db.execute(
        text("DELETE FROM user_pdf_index WHERE user_id = :u"),
        {"u": user_id},
    )
    flags_res = await db.execute(
        text("DELETE FROM chat_abuse_flags WHERE user_id = :u"),
        {"u": user_id},
    )
    ab_res = await db.execute(
        text("DELETE FROM chat_ab_test_assignments WHERE user_id = :u"),
        {"u": user_id},
    )
    quota_res = await db.execute(
        text("DELETE FROM chat_quota_usage WHERE user_id = :u"),
        {"u": user_id},
    )
    # Addon purchases: keep row for billing; null out FK so it's anonymous.
    addons_res = await db.execute(
        text(
            "UPDATE chat_addon_purchases SET user_id = NULL, is_active = FALSE "
            "WHERE user_id = :u"
        ),
        {"u": user_id},
    )
    # Reset abuse / CAPTCHA flags on the user row itself.
    await db.execute(
        text(
            "UPDATE users SET chat_abuse_score = 0, chat_captcha_required = FALSE, "
            "chat_captcha_solve_count = 0, chat_suspended_at = NULL "
            "WHERE id = :u"
        ),
        {"u": user_id},
    )
    await db.commit()
    logger.info(
        "DSAR delete chat-data user=%s convs=%s pdfs=%s flags=%s ab=%s quota=%s addons=%s",
        user_id,
        conv_res.rowcount, pdf_res.rowcount, flags_res.rowcount,
        ab_res.rowcount, quota_res.rowcount, addons_res.rowcount,
    )
    return {
        "data": {
            "ok": True,
            "deleted": {
                "conversations": int(conv_res.rowcount or 0),
                "pdf_index_entries": int(pdf_res.rowcount or 0),
                "abuse_flags": int(flags_res.rowcount or 0),
                "ab_test_assignments": int(ab_res.rowcount or 0),
                "quota_rows": int(quota_res.rowcount or 0),
                "addon_purchases_anonymized": int(addons_res.rowcount or 0),
            },
        }
    }
