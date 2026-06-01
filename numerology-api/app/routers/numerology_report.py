"""Public numerology report endpoint: GET /api/numerology-report.

Returns the full structured JSON report (all indicators) consumed by the
landing-page result screen (/ket-qua). Public — no auth required.

Split from numerology.py for the ≤200 line rule.
"""

import re

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.numerology import calculate_numerology_numbers
from app.deps import get_db
from app.services.numerology_db import get_numerology_models
from app.services.numerology_report_builder import build_report

router = APIRouter()


@router.get("/numerology-report")
async def numerology_report(
    full_name: str = Query(...),
    birth_day: str = Query(...),
    phone: str = Query(default=""),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Full numerology report as JSON — public, no auth required.

    Returns every indicator (số chủ đạo, core numbers, life peaks, challenges,
    personal year/month, missing numbers, power chart) bound to real DB content.
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

    models = await get_numerology_models(db, calc)
    report = build_report(full_name, birth_day, calc, models)
    return {"data": report}
