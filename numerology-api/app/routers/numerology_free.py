"""Public numerology endpoints: free PDF, la-so, debug top.

Split from numerology.py for ≤200 line rule.
"""

import logging
import re
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.numerology import calculate_numerology_numbers
from app.db.models.numerology_content import MainNumber
from app.deps import get_db
from app.services.horoscope_client import gen_horoscopes
from app.services.numerology_context import save_user_download
from app.services.numerology_db import fetch_by_code
from app.services.numerology_full_report import build_report_view
from app.utils.pdf import render_html, render_pdf

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get('/so-chu-dao')
async def so_chu_dao(
    full_name: str = Query(...),
    birth_day: str = Query(...),
    phone: str = Query(default=''),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Mainstream (life-path) number — public, no auth required.

    Returns the MainNumber content row for the computed `so_chu_dao`.
    Consumed by the landing-page result screen (GET /api/so-chu-dao).
    """
    full_name = full_name.strip()
    if not full_name:
        raise HTTPException(400, 'Vui lòng nhập họ tên')
    if not re.fullmatch(r'\d{8}', birth_day):
        raise HTTPException(400, 'Ngày sinh không hợp lệ (định dạng: ddmmyyyy)')

    try:
        calc = calculate_numerology_numbers(birth_day, full_name)
    except ValueError as exc:
        raise HTTPException(400, str(exc))

    row = await fetch_by_code(db, MainNumber, calc['so_chu_dao'])
    if row is None:
        raise HTTPException(404, 'Không tìm thấy dữ liệu số chủ đạo')

    return {
        'data': {
            'so_chu_dao': {
                'id': row.id,
                'code': calc['so_chu_dao'],
                'title': row.title,
                'content': row.content,
                'number_page': row.number_page,
            }
        }
    }


@router.get('/so-hoc-free')
async def so_hoc_free(
    full_name: str = Query(...),
    birth_day: str = Query(...),
    phone: str = Query(...),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """Free numerology PDF — public, no auth required."""
    full_name = full_name.strip()
    if not full_name:
        raise HTTPException(400, 'Vui lòng nhập họ tên')
    if not re.fullmatch(r'\d{8}', birth_day):
        raise HTTPException(400, 'Ngày sinh không hợp lệ (định dạng: ddmmyyyy)')
    phone_digits = re.sub(r'\D', '', phone)
    if len(phone_digits) < 3:
        raise HTTPException(400, 'Số điện thoại không hợp lệ')

    # Save download record before generating PDF (mirrors Django SoHocFreeAPIView)
    await save_user_download(
        db, user_id=None, name=full_name, birth_day=birth_day,
        birth_time=None, gender=None, job=None,
        phone=phone_digits, download_type=0,
    )

    try:
        report = await build_report_view(db, full_name, birth_day, phone_digits)
    except ValueError as exc:
        raise HTTPException(400, str(exc))

    try:
        pdf_bytes = await render_pdf('invoice-free.html', {'report': report})
    except RuntimeError:
        raise HTTPException(500, 'Không thể tạo file PDF, vui lòng thử lại')

    return StreamingResponse(
        iter([pdf_bytes]),
        media_type='application/pdf',
        headers={'Content-Disposition': f'attachment; filename="numerology_free_{birth_day}.pdf"'},
    )


@router.get('/la-so')
async def la_so(
    full_name: str = Query(...),
    birth_day: str = Query(...),
    birth_time: str = Query(...),
    sex: int = Query(default=1),
) -> dict:
    """Astrology chart — proxies to vietheart.net horoscope API.

    Mirrors Django LasoAPIView in views.py:712-729.
    """
    horoscopes = await gen_horoscopes(full_name, birth_day, birth_time, sex)
    return {'data': {'horoscopes': horoscopes}}


@router.get('/')
async def top(
    full_name: str = Query(...),
    birth_day: str = Query(...),
    phone: str = Query(default=''),
    db: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    """Debug HTML preview of invoice.html (mirrors Django top() view)."""
    full_name = full_name.strip()
    if not full_name:
        raise HTTPException(400, 'Vui lòng nhập họ tên')
    if not re.fullmatch(r'\d{8}', birth_day):
        raise HTTPException(400, 'Ngày sinh không hợp lệ')

    try:
        report = await build_report_view(db, full_name, birth_day, phone)
    except ValueError as exc:
        raise HTTPException(400, str(exc))

    return HTMLResponse(content=render_html('invoice.html', {'report': report}))
