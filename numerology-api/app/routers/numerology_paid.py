"""Paid numerology endpoint: GET /api/so-hoc (auth + quota required).

Split from numerology.py for ≤200 line rule.
"""

import logging
import re
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.numerology import calculate_numerology_numbers
from app.db.models.user import User, UserProfile
from app.deps import get_current_user, get_db
from app.services.horoscope_client import gen_horoscopes
from app.services.numerology_context import build_common_context, decrement_quota, save_user_download
from app.services.numerology_db import get_numerology_models
from app.utils.pdf import render_pdf

logger = logging.getLogger(__name__)

router = APIRouter()

# Extra paid param keys — mirrors Django EXTRA_PARAM_KEYS
_EXTRA_KEYS = [
    'r', 'l', 'eq', 'iq', 'aq', 'cq', 'v', 'a', 'k',
    'r1_1', 'r1_2', 'r2_1', 'r2_2', 'r3_1', 'r3_2', 'r4_1', 'r4_2', 'r5_1', 'r5_2',
    'l1_1', 'l1_2', 'l2_1', 'l2_2', 'l3_1', 'l3_2', 'l4_1', 'l4_2', 'l5_1', 'l5_2',
    'type_iq_1', 'type_iq_2', 'type_iq_3', 'type_iq_4',
    'type_iq_5', 'type_iq_6', 'type_iq_7', 'type_iq_8',
]


def _parse_birth_time_hm(birth_time_raw: Optional[str]) -> Optional[str]:
    """Parse raw birth_time string → 'HH:MM'. Silent None on failure."""
    if not birth_time_raw:
        return None
    try:
        import datetime as dt
        time_part = birth_time_raw.split(' ')[4]
        parsed = dt.datetime.strptime(time_part, '%H:%M:%S') + dt.timedelta(hours=7)
        return parsed.strftime('%H:%M')
    except (IndexError, ValueError):
        return None


@router.get('/so-hoc')
async def so_hoc(
    full_name: str = Query(...),
    birth_day: str = Query(...),
    phone: str = Query(...),
    sex: int = Query(default=1),
    birth_time: Optional[str] = Query(default=None),
    job: Optional[str] = Query(default=None),
    r: str = Query(default=''), l: str = Query(default=''),
    eq: str = Query(default=''), iq: str = Query(default=''),
    aq: str = Query(default=''), cq: str = Query(default=''),
    v: str = Query(default=''), a: str = Query(default=''), k: str = Query(default=''),
    r1_1: str = Query(default=''), r1_2: str = Query(default=''),
    r2_1: str = Query(default=''), r2_2: str = Query(default=''),
    r3_1: str = Query(default=''), r3_2: str = Query(default=''),
    r4_1: str = Query(default=''), r4_2: str = Query(default=''),
    r5_1: str = Query(default=''), r5_2: str = Query(default=''),
    l1_1: str = Query(default=''), l1_2: str = Query(default=''),
    l2_1: str = Query(default=''), l2_2: str = Query(default=''),
    l3_1: str = Query(default=''), l3_2: str = Query(default=''),
    l4_1: str = Query(default=''), l4_2: str = Query(default=''),
    l5_1: str = Query(default=''), l5_2: str = Query(default=''),
    type_iq_1: str = Query(default=''), type_iq_2: str = Query(default=''),
    type_iq_3: str = Query(default=''), type_iq_4: str = Query(default=''),
    type_iq_5: str = Query(default=''), type_iq_6: str = Query(default=''),
    type_iq_7: str = Query(default=''), type_iq_8: str = Query(default=''),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StreamingResponse:
    """Paid numerology PDF. Auth required + number_download >= 1."""
    full_name = full_name.strip()
    if not full_name:
        raise HTTPException(400, 'Vui lòng nhập họ tên')
    if not re.fullmatch(r'\d{8}', birth_day):
        raise HTTPException(400, 'Ngày sinh không hợp lệ (định dạng: ddmmyyyy)')

    result = await db.execute(select(UserProfile).where(UserProfile.user_id == current_user.id))
    profile = result.scalar_one_or_none()
    if not profile or profile.number_download < 1:
        raise HTTPException(400, 'Bạn không đủ lượt tải')

    horoscopes = None
    if birth_time:
        try:
            horoscopes = await gen_horoscopes(full_name, birth_day, birth_time, sex)
        except HTTPException:
            horoscopes = None  # non-fatal

    try:
        calc = calculate_numerology_numbers(birth_day, full_name)
    except ValueError as exc:
        raise HTTPException(400, str(exc))

    models = await get_numerology_models(db, calc)
    context = build_common_context(full_name, birth_day, phone, calc, models)
    context.update({
        'r': r, 'l': l, 'eq': eq, 'iq': iq, 'aq': aq, 'cq': cq,
        'v': v, 'a': a, 'k': k,
        'r1_1': r1_1, 'r1_2': r1_2, 'r2_1': r2_1, 'r2_2': r2_2,
        'r3_1': r3_1, 'r3_2': r3_2, 'r4_1': r4_1, 'r4_2': r4_2,
        'r5_1': r5_1, 'r5_2': r5_2,
        'l1_1': l1_1, 'l1_2': l1_2, 'l2_1': l2_1, 'l2_2': l2_2,
        'l3_1': l3_1, 'l3_2': l3_2, 'l4_1': l4_1, 'l4_2': l4_2,
        'l5_1': l5_1, 'l5_2': l5_2,
        'type_iq_1': type_iq_1, 'type_iq_2': type_iq_2,
        'type_iq_3': type_iq_3, 'type_iq_4': type_iq_4,
        'type_iq_5': type_iq_5, 'type_iq_6': type_iq_6,
        'type_iq_7': type_iq_7, 'type_iq_8': type_iq_8,
        'horoscopes': horoscopes,
    })

    try:
        pdf_bytes = await render_pdf('invoice.html', context)
    except RuntimeError:
        raise HTTPException(500, 'Không thể tạo file PDF, vui lòng thử lại')

    # Deduct quota + save record only after successful PDF generation
    await decrement_quota(db, current_user.id)
    await save_user_download(
        db, user_id=current_user.id, name=full_name, birth_day=birth_day,
        birth_time=_parse_birth_time_hm(birth_time),
        gender=str(sex) if sex else None, job=job, phone=phone, download_type=1,
    )

    return StreamingResponse(
        iter([pdf_bytes]),
        media_type='application/pdf',
        headers={'Content-Disposition': f'attachment; filename="numerology_{birth_day}.pdf"'},
    )
