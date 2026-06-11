"""Numerology DB query helpers — async SQLAlchemy 2.0.

Fetches content rows used by templates.
Ported from Django ORM calls in views.py:get_numerology_models() and SoHocFreeAPIView.
"""

from __future__ import annotations

from typing import Any, Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.numerology_content import (
    AttitudeNumber, BirthdayChart, BirthdayNumber,
    ChallengeLife, DevelopmentNumber, Identifiable,
    IntrospectiveNumber, KarmicNumber, LifePeak, MainNumber, MatureNumber,
    MissNumber, MissionNumber, PersonalMonthNumber,
    PhoneNumber, SoulsNumber, StagesOfLife,
)


async def fetch_by_code(db: AsyncSession, model_cls: type, code: Any) -> Optional[Any]:
    """Fetch single content row by code. Returns None if not found."""
    result = await db.execute(
        select(model_cls).where(model_cls.code == str(code))
    )
    return result.scalar_one_or_none()


async def fetch_many_by_codes(
    db: AsyncSession, model_cls: type, codes: Sequence[Any]
) -> list[Any]:
    """Fetch multiple content rows matching any of the given codes."""
    if not codes:
        return []
    result = await db.execute(
        select(model_cls).where(model_cls.code.in_([str(c) for c in codes]))
    )
    return list(result.scalars().all())


async def get_numerology_models(db: AsyncSession, calc: dict) -> dict:
    """Bulk-fetch all content rows needed by templates.

    Mirrors Django get_numerology_models() in views.py:234-289.
    """
    miss_rows = await fetch_many_by_codes(db, MissNumber, calc['leak_num'])
    return {
        'life_peak_1': await fetch_by_code(db, LifePeak, calc['dinh_cao_1']),
        'life_peak_2': await fetch_by_code(db, LifePeak, calc['dinh_cao_2']),
        'life_peak_3': await fetch_by_code(db, LifePeak, calc['dinh_cao_3']),
        'life_peak_4': await fetch_by_code(db, LifePeak, calc['dinh_cao_4']),
        'for_peak': await fetch_by_code(db, LifePeak, 1000),
        'challenge_life_1': await fetch_by_code(db, ChallengeLife, calc['thu_thach_1']),
        'challenge_life_2': await fetch_by_code(db, ChallengeLife, calc['thu_thach_2']),
        'challenge_life_3': await fetch_by_code(db, ChallengeLife, calc['thu_thach_3']),
        'challenge_life_4': await fetch_by_code(db, ChallengeLife, calc['thu_thach_4']),
        'main_number_data': await fetch_by_code(db, MainNumber, calc['so_chu_dao']),
        'attitude_number': await fetch_by_code(db, AttitudeNumber, calc['so_thai_do']),
        'birth_number': await fetch_by_code(db, BirthdayNumber, calc['so_ngay_sinh']),
        'mission_number': await fetch_by_code(db, MissionNumber, calc['so_su_menh']),
        'development_number': await fetch_by_code(db, DevelopmentNumber, calc['so_truong_thanh']),
        'karmic_number': await fetch_by_code(db, KarmicNumber, calc['so_noi_cam']),
        'mature_number': await fetch_by_code(db, MatureNumber, calc['so_nhan_cach']),
        'souls_number': await fetch_by_code(db, SoulsNumber, calc['so_linh_hon']),
        'personal_month_number': await fetch_by_code(db, PersonalMonthNumber, calc['so_thang_ca_nhan']),
        'miss_number': miss_rows,
    }


async def get_free_extra_models(db: AsyncSession, birth_day: str, phone: str) -> dict:
    """Fetch extra DB rows needed only by invoice-free.html.

    Mirrors SoHocFreeAPIView logic in views.py:580-607.
    """
    three_phone = phone[-3:]
    r1 = await db.execute(select(PhoneNumber).where(PhoneNumber.code.contains(three_phone[:2])))
    r2 = await db.execute(select(PhoneNumber).where(PhoneNumber.code.contains(three_phone[-2:])))

    chart_results: dict[str, Any] = {}
    for pat in ('123', '147', '159', '258', '357', '369', '456', '789'):
        digits = list(pat)
        if all(birth_day.count(d) for d in digits):
            chart_results[f'char_birth_day_all_{pat}'] = await fetch_by_code(db, BirthdayChart, pat)
        else:
            chart_results[f'char_birth_day_all_{pat}'] = None

    return {
        'two_first_phone': r1.scalar_one_or_none(),
        'two_last_phone': r2.scalar_one_or_none(),
        'stages_of_life_1': await fetch_by_code(db, StagesOfLife, 1),
        'stages_of_life_2': await fetch_by_code(db, StagesOfLife, 2),
        'stages_of_life_3': await fetch_by_code(db, StagesOfLife, 3),
        'char_birth_not': await fetch_by_code(db, BirthdayChart, '20  '),
        **chart_results,
    }
