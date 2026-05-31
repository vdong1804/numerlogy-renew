"""Async HTTP client for vietheart.net horoscope API.

Ported from numerology/apis/utils.py:gen_horoscopes().
Converts sync requests → async httpx with timeout + error handling.
"""

import datetime
from typing import Any

import httpx
from fastapi import HTTPException

# Hour-of-birth lookup table — maps real clock hour → API hour_of_birth id
# e.g. hour 1..2 → id=2, hour 3..4 → id=4, etc.
_HOURS = [
    {'id': 2,  'min': 1,  'max': 3},
    {'id': 4,  'min': 3,  'max': 5},
    {'id': 6,  'min': 5,  'max': 7},
    {'id': 8,  'min': 7,  'max': 9},
    {'id': 10, 'min': 9,  'max': 11},
    {'id': 12, 'min': 11, 'max': 13},
    {'id': 14, 'min': 13, 'max': 15},
    {'id': 16, 'min': 15, 'max': 17},
    {'id': 18, 'min': 17, 'max': 19},
    {'id': 20, 'min': 19, 'max': 21},
    {'id': 22, 'min': 21, 'max': 23},
]

_API_URL = 'https://api.vietheart.net/api/v1/horoscopes/create/'


def _resolve_hour_id(hour: int) -> int:
    """Map birth hour (0-23) to vietheart API hour_of_birth id."""
    for entry in _HOURS:
        if entry['min'] <= hour < entry['max']:
            return entry['id']
    return 0  # midnight / unmatched → 0 (matches Django fallback)


async def gen_horoscopes(
    full_name: str,
    birth_day: str,
    birth_time: str,
    sex: int,
) -> Any:
    """Call vietheart.net horoscope API and return image data.

    Args:
        full_name: person's full name
        birth_day: 8-digit ddmmyyyy string
        birth_time: raw birth_time string from request — format 'X X X X HH:MM:SS'
                    (5th space-separated token is time, then +7h offset applied)
        sex: 1=male, 2=female

    Returns:
        image data from API response data.data.data

    Raises:
        HTTPException 400: birth_time format unrecognisable
        HTTPException 503: vietheart.net unreachable or returned error
    """
    # Parse birth_time — ported from views.py:parse_birth_time()
    import datetime as dt
    try:
        time_part = birth_time.split(' ')[4]
        parsed_time = datetime.datetime.strptime(time_part, '%H:%M:%S')
        parsed_time = parsed_time + dt.timedelta(hours=7)
        birth_time_hour = parsed_time.hour
    except (IndexError, ValueError):
        raise HTTPException(status_code=400, detail='Định dạng giờ sinh không hợp lệ')

    day = birth_day[0:2]
    month = birth_day[2:4]
    year = birth_day[4:8]
    date_of_birth = f'{day}-{month}-{year}'

    hour_of_birth = _resolve_hour_id(birth_time_hour)

    payload = {
        'name': full_name,
        'type': 2,
        'sex': int(sex),
        'date_of_birth': date_of_birth,
        'hour_of_birth': hour_of_birth,
        'year_of_view': datetime.datetime.now().year,
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(_API_URL, json=payload)
            response.raise_for_status()
            data = response.json()
            return data['data']['data']
    except httpx.TimeoutException:
        raise HTTPException(status_code=503, detail='Horoscope service unavailable (timeout)')
    except (httpx.HTTPError, KeyError, ValueError):
        raise HTTPException(status_code=503, detail='Horoscope service unavailable')
