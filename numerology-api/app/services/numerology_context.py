"""Numerology context builder + download/quota persistence.

Ported from views.py:build_common_context(), SoHocAPIView, SoHocFreeAPIView.
Pure context building has no DB calls; save/decrement are async.
"""

from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.download import UserDownload
from app.db.models.user import UserProfile


def build_common_context(
    full_name: str,
    birth_day: str,
    phone: str,
    calc: dict,
    models: dict,
) -> dict:
    """Build Jinja2 template context dict.

    Ported verbatim from views.py:292-365. Pure function — no DB, no async.
    """
    text_name = calc['text_name']
    leak_num = calc['leak_num']

    ctx: dict[str, Any] = {
        'name': full_name.upper(),
        'birth_day': birth_day,
        'birth_day_text': f"{birth_day[:2]}/{birth_day[2:4]}/{birth_day[4:]}",
        # Birthday digit occurrence strings
        **{f'char_birth_day_{d}': str(d) * birth_day.count(str(d)) for d in range(1, 10)},
        # Name digit occurrence strings
        **{f'char_name_{d}': str(d) * text_name.count(str(d)) for d in range(1, 10)},
        # Core numerology numbers
        'so_chu_dao': calc['so_chu_dao'],
        'so_thai_do': calc['so_thai_do'],
        'so_ngay_sinh': calc['so_ngay_sinh'],
        'so_thang_sinh': calc['so_thang_sinh'],
        'so_nam_sinh': calc['so_nam_sinh'],
        'so_su_menh': calc['so_su_menh'],
        'so_thuc_thi': calc['so_thuc_thi'],
        'so_can_bang': calc['so_can_bang'],
        'so_linh_hon': calc['so_linh_hon'],
        'so_nhan_cach': calc['so_nhan_cach'],
        'so_truong_thanh': calc['so_truong_thanh'],
        'so_phat_trien': calc['so_phat_trien'],
        'so_noi_cam': calc['so_noi_cam'],
        'the_nhan_dang': calc['the_nhan_dang'],
        'so_nam_ca_nhan': calc['so_nam_ca_nhan'],
        'so_thang_ca_nhan': calc['so_thang_ca_nhan'],
        'stages': calc['stages'],
        'tuoi_dinh_cao_1': calc['tuoi_dinh_cao_1'],
        'tuoi_dinh_cao_2': calc['tuoi_dinh_cao_2'],
        'tuoi_dinh_cao_3': calc['tuoi_dinh_cao_3'],
        'tuoi_dinh_cao_4': calc['tuoi_dinh_cao_4'],
        'dinh_cao_1': calc['dinh_cao_1'],
        'dinh_cao_2': calc['dinh_cao_2'],
        'dinh_cao_3': calc['dinh_cao_3'],
        'dinh_cao_4': calc['dinh_cao_4'],
        'thu_thach_1': calc['thu_thach_1'],
        'thu_thach_2': calc['thu_thach_2'],
        'thu_thach_3': calc['thu_thach_3'],
        'thu_thach_4': calc['thu_thach_4'],
        'so_thieu': ','.join(str(x) for x in leak_num),
        **models,
    }

    # Phone digits — strip non-digits, strip leading 84 country code, pad to 10
    if phone:
        digits = ''.join(c for c in phone if c.isdigit())
        if digits.startswith('84') and len(digits) >= 11:
            digits = '0' + digits[2:]
        digits = digits[-10:] if len(digits) >= 10 else digits.rjust(10, ' ')
        ctx.update({f'phone_{i + 1}': digits[i] for i in range(10)})

    return ctx


async def save_user_download(
    db: AsyncSession,
    user_id: Optional[int],
    name: str,
    birth_day: str,
    birth_time: Optional[str],
    gender: Optional[str],
    job: Optional[str],
    phone: str,
    download_type: int,
) -> UserDownload:
    """Insert a UserDownload record and return it."""
    day, month, year = birth_day[:2], birth_day[2:4], birth_day[4:]
    row = UserDownload(
        user_id=user_id,
        name=name,
        birth_day=f'{day}/{month}/{year}',
        birth_time=birth_time,
        gender=str(gender) if gender is not None else None,
        job=job,
        phone=phone,
        type=download_type,
    )
    db.add(row)
    await db.flush()
    return row


async def decrement_quota(db: AsyncSession, user_id: int) -> None:
    """Decrement number_download by 1 using SELECT FOR UPDATE (prevents race conditions)."""
    result = await db.execute(
        select(UserProfile)
        .where(UserProfile.user_id == user_id)
        .with_for_update()
    )
    profile = result.scalar_one_or_none()
    if profile and profile.number_download > 0:
        profile.number_download -= 1
        await db.flush()
