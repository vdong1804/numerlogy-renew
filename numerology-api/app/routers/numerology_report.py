"""Public numerology report endpoint: GET /api/numerology-report.

Returns the full structured JSON report (all indicators) consumed by the
landing-page result screen (/ket-qua). Public — no auth required.

Split from numerology.py for the ≤200 line rule.
"""

import re
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.numerology import calculate_numerology_numbers
from app.db.models.user import User
from app.deps import get_current_user_optional, get_db
from app.services.numerology_db import get_numerology_models
from app.services.numerology_report_builder import build_report
from app.services.report_entitlement_service import (
    find_order_report_download_id,
    resolve_entitlement,
)

router = APIRouter()


@router.get("/numerology-report")
async def numerology_report(
    full_name: str = Query(...),
    birth_day: str = Query(...),
    phone: str = Query(default=""),
    db: AsyncSession = Depends(get_db),
    user: Optional[User] = Depends(get_current_user_optional),
) -> dict:
    """Numerology report as JSON — public; personalizes when a valid token is sent.

    Returns every indicator (số chủ đạo, core numbers, life peaks, challenges,
    personal year/month, missing numbers, power chart) bound to real DB content.
    Free viewers receive only the unlocked sections in full; locked sections have
    their interpretation stripped server-side (content=null, locked=true) so paid
    content never reaches an unentitled client.
    """
    full_name = full_name.strip()
    if not full_name:
        raise HTTPException(400, "Vui lòng nhập họ tên")
    if not re.fullmatch(r"\d{8}", birth_day):
        raise HTTPException(400, "Ngày sinh không hợp lệ (định dạng: ddmmyyyy)")

    try:
        calc = calculate_numerology_numbers(birth_day, full_name)
    except ValueError as exc:
        raise HTTPException(400, str(exc))

    tier, unlocked, matched_order_id = await resolve_entitlement(
        db, user, full_name, birth_day
    )
    # Paid viewers get the download id of their already-fulfilled PDF (if any) so
    # the UI can link to GET /api/my/reports/{id}/download.
    report_download_id = (
        await find_order_report_download_id(db, matched_order_id)
        if matched_order_id is not None
        else None
    )
    models = await get_numerology_models(db, calc)
    report = build_report(full_name, birth_day, calc, models, unlocked)
    return {
        "data": report,
        "tier": tier,
        "unlocked": sorted(unlocked),
        "matched_order_id": matched_order_id,
        "report_download_id": report_download_id,
    }
