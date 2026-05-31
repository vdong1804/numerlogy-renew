"""Pure numerology calculation — zero DB, zero framework.

Inputs:
    birth_day: str  — 8-digit ddmmyyyy e.g. "15101990"
    full_name: str  — Vietnamese full name (accented or plain)
    current_age: int | None — override age (useful in tests)

Returns dict with all numerology numbers (see calculate_numerology_numbers).

Master-number redirect rules (ported from views.py lines 121-124, 159-160, 186-187):
  - thu_thach_* == 0  → redirect to 9  (DB has no code=0 row)
  - so_thuc_thi == 0  → redirect to 9  (DB has no code=0 row)
  - so_truong_thanh ∈ {11,22,33} → reduce  (DB has no master entries for this field)
"""

from __future__ import annotations

from datetime import datetime
from statistics import mode
from typing import Optional

from app.core.alphabet import alphabet, strip_accents
from app.core.numerology_sums import get_sum, get_sum_new, get_sum_spec

# Re-export sum helpers so callers can do: from app.core.numerology import get_sum
__all__ = [
    "calculate_numerology_numbers",
    "get_sum", "get_sum_spec", "get_sum_new",
]


def calculate_numerology_numbers(
    birth_day: str,
    full_name: str,
    current_age: Optional[int] = None,
) -> dict:
    """Calculate all numerology numbers.

    Raises ValueError if name has no mappable alphabet characters.
    """
    day_sum = get_sum_new(int(birth_day[0:2]))
    month_sum = get_sum_new(int(birth_day[2:4]))
    year_sum = get_sum_new(int(birth_day[4:8]))
    sum_birth_day = sum(int(x) for x in birth_day if x.isdigit())

    so_chu_dao = get_sum_spec(day_sum + month_sum + year_sum)

    sum_ngay = int(birth_day[0]) + int(birth_day[1])
    sum_thang = int(birth_day[2]) + int(birth_day[3])
    so_ngay_sinh = get_sum(sum_ngay)
    so_thang_sinh = get_sum(sum_thang)
    so_nam_sinh = get_sum(sum_birth_day - sum_thang - sum_ngay)
    so_thai_do = get_sum(so_ngay_sinh + so_thang_sinh)

    tuoi_dinh_cao_1 = 36 - so_chu_dao
    tuoi_dinh_cao_2 = tuoi_dinh_cao_1 + 9
    tuoi_dinh_cao_3 = tuoi_dinh_cao_2 + 9
    tuoi_dinh_cao_4 = tuoi_dinh_cao_3 + 9

    age = current_age if current_age is not None else (datetime.now().year - int(birth_day[4:8]))

    dinh_cao_1 = get_sum(get_sum(so_ngay_sinh + so_thang_sinh))
    dinh_cao_2 = get_sum(get_sum(so_ngay_sinh + so_nam_sinh))
    dinh_cao_3 = get_sum(dinh_cao_1 + dinh_cao_2)
    dinh_cao_4 = get_sum(so_thang_sinh + so_nam_sinh)

    stages, tuoi_dinh_cao = 0, None
    if age > (25 - so_chu_dao) and age < tuoi_dinh_cao_1:
        stages, tuoi_dinh_cao = dinh_cao_1, tuoi_dinh_cao_1
    if age >= tuoi_dinh_cao_1 and age < tuoi_dinh_cao_2:
        stages, tuoi_dinh_cao = dinh_cao_2, tuoi_dinh_cao_2
    if age >= tuoi_dinh_cao_2 and age < tuoi_dinh_cao_3:
        stages, tuoi_dinh_cao = dinh_cao_3, tuoi_dinh_cao_3
    if age >= tuoi_dinh_cao_3 and age < 54 + so_chu_dao:
        stages, tuoi_dinh_cao = dinh_cao_4, tuoi_dinh_cao_4

    so_nam_ca_nhan = so_thang_ca_nhan = None
    if age > (25 - so_chu_dao) and age < 54 + so_chu_dao:
        so_nam_ca_nhan = 9 - tuoi_dinh_cao + age
        # Wrap negative into 1-9 cycle (views.py line 99: if < 0: += 9)
        if so_nam_ca_nhan < 0:
            so_nam_ca_nhan += 9
        so_nam_ca_nhan = get_sum(so_nam_ca_nhan)
        so_thang_ca_nhan = get_sum(so_nam_ca_nhan + datetime.now().month)
    if age <= (25 - so_chu_dao):
        so_nam_ca_nhan, so_thang_ca_nhan = 11, get_sum(datetime.now().month)
    if age >= (54 + so_chu_dao):
        so_nam_ca_nhan, so_thang_ca_nhan = 10, get_sum(datetime.now().month)
    if so_nam_ca_nhan == 0:
        so_nam_ca_nhan = 9

    # 4 thách thức — MASTER-NUMBER REDIRECT: 0 → 9 (views.py lines 121-124)
    thu_thach_1 = get_sum(get_sum(get_sum(abs(so_ngay_sinh - so_thang_sinh))))
    thu_thach_2 = get_sum(get_sum(abs(so_ngay_sinh - so_nam_sinh)))
    thu_thach_3 = get_sum(get_sum(abs(thu_thach_1 - thu_thach_2)))
    thu_thach_4 = get_sum(get_sum(abs(so_nam_sinh - so_thang_sinh)))
    if thu_thach_1 == 0: thu_thach_1 = 9
    if thu_thach_2 == 0: thu_thach_2 = 9
    if thu_thach_3 == 0: thu_thach_3 = 9
    if thu_thach_4 == 0: thu_thach_4 = 9

    # Name analysis
    full_name_lower = strip_accents(full_name).lower()
    name_parts = full_name_lower.split()
    if not name_parts:
        raise ValueError("full_name has no recognizable characters after accent stripping")
    ho, ten = name_parts[0], name_parts[-1]

    sum_full_name = sum_full_vowel = sum_full_consonant = 0
    arr_value: list[int] = []
    for char in full_name_lower:
        if char in alphabet:
            info = alphabet[char]
            if info['is_vowel']:
                sum_full_vowel += info['value']
            else:
                sum_full_consonant += info['value']
            sum_full_name += info['value']
            arr_value.append(info['value'])

    if not arr_value:
        raise ValueError("full_name contains no mappable alphabet characters")

    text_name = ''.join(str(v) for v in arr_value)
    so_can_bang = get_sum((alphabet.get(ho[0], {}).get('value', 0)) + (alphabet.get(ten[0], {}).get('value', 0)))
    so_linh_hon = get_sum_spec(get_sum_spec(sum_full_vowel))
    so_su_menh = get_sum_spec(get_sum_spec(sum_full_name))

    # MASTER-NUMBER REDIRECT: Thực Thi 0 → 9 (views.py lines 159-160)
    so_thuc_thi = abs(get_sum(so_chu_dao) - get_sum(so_su_menh))
    if so_thuc_thi == 0: so_thuc_thi = 9

    so_nhan_cach = get_sum_spec(get_sum_spec(sum_full_consonant))

    sum_name, the_nhan_dang = 0, ''
    for char in ten:
        if char in alphabet:
            info = alphabet[char]
            if info['is_vowel'] and not the_nhan_dang:
                the_nhan_dang = info['value']
            sum_name += info['value']

    so_phat_trien = get_sum_spec(get_sum_spec(sum_name))

    # MASTER-NUMBER REDIRECT: Trưởng Thành {11,22,33} → reduce (views.py lines 186-187)
    so_truong_thanh = get_sum_spec(so_su_menh + get_sum(so_chu_dao))
    if so_truong_thanh in (11, 22, 33):
        so_truong_thanh = get_sum(so_truong_thanh)

    so_noi_cam = mode(arr_value)
    leak_num = [n for n in range(1, 10) if str(n) not in text_name]

    return {
        'so_chu_dao': so_chu_dao, 'so_ngay_sinh': so_ngay_sinh,
        'so_thang_sinh': so_thang_sinh, 'so_nam_sinh': so_nam_sinh,
        'so_thai_do': so_thai_do,
        'tuoi_dinh_cao_1': tuoi_dinh_cao_1, 'tuoi_dinh_cao_2': tuoi_dinh_cao_2,
        'tuoi_dinh_cao_3': tuoi_dinh_cao_3, 'tuoi_dinh_cao_4': tuoi_dinh_cao_4,
        'age': age, 'dinh_cao_1': dinh_cao_1, 'dinh_cao_2': dinh_cao_2,
        'dinh_cao_3': dinh_cao_3, 'dinh_cao_4': dinh_cao_4,
        'stages': stages, 'tuoi_dinh_cao': tuoi_dinh_cao,
        'so_nam_ca_nhan': so_nam_ca_nhan, 'so_thang_ca_nhan': so_thang_ca_nhan,
        'thu_thach_1': thu_thach_1, 'thu_thach_2': thu_thach_2,
        'thu_thach_3': thu_thach_3, 'thu_thach_4': thu_thach_4,
        'so_can_bang': so_can_bang, 'so_linh_hon': so_linh_hon,
        'so_su_menh': so_su_menh, 'so_thuc_thi': so_thuc_thi,
        'so_nhan_cach': so_nhan_cach, 'so_phat_trien': so_phat_trien,
        'so_truong_thanh': so_truong_thanh, 'so_noi_cam': so_noi_cam,
        'text_name': text_name, 'the_nhan_dang': the_nhan_dang, 'leak_num': leak_num,
    }
