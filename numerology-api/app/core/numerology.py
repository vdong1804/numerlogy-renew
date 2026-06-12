"""Pure numerology calculation — zero DB, zero framework.

Algorithm mirrors the authoritative Excel template (SAMPLE 00.00.2000.xls),
sheets `NGÀY SINH`, `TÊN`, `Full`. Only numbers present in that template are
computed; fields with no Excel counterpart (số cân bằng, số thực thi) were
removed.

Inputs:
    birth_day: str  — 8-digit ddmmyyyy e.g. "15101990"
    full_name: str  — Vietnamese full name (accented or plain)
    current_age: int | None — override age (used only to pick the active life peak)

Returns dict with all numerology numbers (see calculate_numerology_numbers).

Reduction policy (matches content-table code ranges in scripts/_content_codes.py):
  - MASTER (preserve 11/22/33, via get_sum_spec): chủ đạo, sứ mệnh, linh hồn,
    nhân cách, phát triển.
  - BASIC (reduce to 1-9, via get_sum): everything else.
  - Redirect 0 → 9 for challenges / personal-year (DB has no code=0 row).
"""

from __future__ import annotations

from datetime import datetime
from statistics import mode
from typing import Optional

from app.core.alphabet import alphabet, strip_accents
from app.core.numerology_chart import derive_chart_fields
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
    # ── Birth-date numbers (sheet NGÀY SINH) ────────────────────────────
    day_sum = get_sum_new(int(birth_day[0:2]))
    month_sum = get_sum_new(int(birth_day[2:4]))
    year_sum = get_sum_new(int(birth_day[4:8]))
    sum_birth_day = sum(int(x) for x in birth_day if x.isdigit())

    so_chu_dao = get_sum_spec(day_sum + month_sum + year_sum)  # N3 = SUM(B3:I3) reduced

    sum_ngay = int(birth_day[0]) + int(birth_day[1])
    sum_thang = int(birth_day[2]) + int(birth_day[3])
    so_ngay_sinh = get_sum(sum_ngay)                                  # N4
    so_thang_sinh = get_sum(sum_thang)                                # N5
    so_nam_sinh = get_sum(sum_birth_day - sum_thang - sum_ngay)       # N6
    so_thai_do = get_sum(so_ngay_sinh + so_thang_sinh)               # N7 = N4+N5

    # ── 4 life peaks: ages (C12:F12) + values (N12:N15) ─────────────────
    tuoi_dinh_cao_1 = 36 - so_chu_dao
    tuoi_dinh_cao_2 = tuoi_dinh_cao_1 + 9
    tuoi_dinh_cao_3 = tuoi_dinh_cao_2 + 9
    tuoi_dinh_cao_4 = tuoi_dinh_cao_3 + 9

    age = current_age if current_age is not None else (datetime.now().year - int(birth_day[4:8]))

    dinh_cao_1 = get_sum(get_sum(so_ngay_sinh + so_thang_sinh))  # N12 = N4+N5
    dinh_cao_2 = get_sum(get_sum(so_ngay_sinh + so_nam_sinh))    # N13 = N4+N6
    dinh_cao_3 = get_sum(dinh_cao_1 + dinh_cao_2)               # N14 = N12+N13
    dinh_cao_4 = get_sum(so_thang_sinh + so_nam_sinh)           # N15 = N5+N6

    # Active peak for the current age (selects which of the 4 peaks applies now)
    stages, tuoi_dinh_cao = 0, None
    if age > (25 - so_chu_dao) and age < tuoi_dinh_cao_1:
        stages, tuoi_dinh_cao = dinh_cao_1, tuoi_dinh_cao_1
    if age >= tuoi_dinh_cao_1 and age < tuoi_dinh_cao_2:
        stages, tuoi_dinh_cao = dinh_cao_2, tuoi_dinh_cao_2
    if age >= tuoi_dinh_cao_2 and age < tuoi_dinh_cao_3:
        stages, tuoi_dinh_cao = dinh_cao_3, tuoi_dinh_cao_3
    if age >= tuoi_dinh_cao_3 and age < 54 + so_chu_dao:
        stages, tuoi_dinh_cao = dinh_cao_4, tuoi_dinh_cao_4

    # ── Personal month (Excel: K10 = N8 + tháng) ────────────────────────
    # Số năm cá nhân (= reduce(số năm thế giới + số thái độ)) is kept ONLY as
    # an internal intermediate for số tháng cá nhân — it is no longer exposed.
    now = datetime.now()
    so_nam_ca_nhan = get_sum(get_sum(now.year) + so_thai_do) or 9
    so_thang_ca_nhan = get_sum(so_nam_ca_nhan + now.month)

    # ── 4 challenges (N16:N19), redirect 0 → 9 ──────────────────────────
    thu_thach_1 = get_sum(get_sum(get_sum(abs(so_ngay_sinh - so_thang_sinh))))  # K16 = |N4-N5|
    thu_thach_2 = get_sum(get_sum(abs(so_ngay_sinh - so_nam_sinh)))             # K17 = |N4-N6|
    thu_thach_3 = get_sum(get_sum(abs(thu_thach_1 - thu_thach_2)))             # K18 = |K16-K17|
    thu_thach_4 = get_sum(get_sum(abs(so_nam_sinh - so_thang_sinh)))           # K19 = |N6-N5|
    if thu_thach_1 == 0: thu_thach_1 = 9
    if thu_thach_2 == 0: thu_thach_2 = 9
    if thu_thach_3 == 0: thu_thach_3 = 9
    if thu_thach_4 == 0: thu_thach_4 = 9

    # ── Name numbers (sheet TÊN) ────────────────────────────────────────
    full_name_lower = strip_accents(full_name).lower()
    name_parts = full_name_lower.split()
    if not name_parts:
        raise ValueError("full_name has no recognizable characters after accent stripping")
    ten = name_parts[-1]  # given name = last word

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
    so_linh_hon = get_sum_spec(get_sum_spec(sum_full_vowel))      # AB2 — vowels of full name
    so_su_menh = get_sum_spec(get_sum_spec(sum_full_name))        # AB3 — all letters of full name
    so_nhan_cach = get_sum_spec(get_sum_spec(sum_full_consonant)) # AB4 — consonants of full name

    # Given-name (Tên riêng) numbers
    sum_name, the_nhan_dang = 0, ''
    for char in ten:
        if char in alphabet:
            info = alphabet[char]
            if info['is_vowel'] and not the_nhan_dang:
                the_nhan_dang = info['value']  # AB9 — first vowel of given name
            sum_name += info['value']

    so_phat_trien = get_sum_spec(get_sum_spec(sum_name))  # AB11 — all letters of given name

    # Số trưởng thành (AB14) = sứ mệnh + chủ đạo; reduce master → basic per DevelopmentNumber
    so_truong_thanh = get_sum_spec(so_su_menh + get_sum(so_chu_dao))
    if so_truong_thanh in (11, 22, 33):
        so_truong_thanh = get_sum(so_truong_thanh)

    so_noi_cam = mode(arr_value)  # most frequent value in the name chart

    # ── Số thiếu (Excel: missing in birth date + full name + 7 core numbers) ──
    core_digits = {
        str(get_sum(n)) for n in (
            so_chu_dao, so_su_menh, so_linh_hon, so_nhan_cach,
            so_ngay_sinh, so_thai_do, so_truong_thanh,
        )
    }
    present = set(birth_day) | set(text_name) | core_digits
    leak_num = [n for n in range(1, 10) if str(n) not in present]

    # ── Birth/name-chart report fields (G1-G6): arrows, isolated, karmic debt… ──
    chart_fields = derive_chart_fields(
        birth_day, text_name, day_sum + month_sum + year_sum,
        sum_full_name, sum_full_vowel, sum_full_consonant,
    )

    return {
        'so_chu_dao': so_chu_dao, 'so_ngay_sinh': so_ngay_sinh,
        'so_thang_sinh': so_thang_sinh, 'so_nam_sinh': so_nam_sinh,
        'so_thai_do': so_thai_do,
        'tuoi_dinh_cao_1': tuoi_dinh_cao_1, 'tuoi_dinh_cao_2': tuoi_dinh_cao_2,
        'tuoi_dinh_cao_3': tuoi_dinh_cao_3, 'tuoi_dinh_cao_4': tuoi_dinh_cao_4,
        'age': age, 'dinh_cao_1': dinh_cao_1, 'dinh_cao_2': dinh_cao_2,
        'dinh_cao_3': dinh_cao_3, 'dinh_cao_4': dinh_cao_4,
        'stages': stages, 'tuoi_dinh_cao': tuoi_dinh_cao,
        'so_nam_ca_nhan': so_nam_ca_nhan,
        'so_thang_ca_nhan': so_thang_ca_nhan,
        'thu_thach_1': thu_thach_1, 'thu_thach_2': thu_thach_2,
        'thu_thach_3': thu_thach_3, 'thu_thach_4': thu_thach_4,
        'so_linh_hon': so_linh_hon,
        'so_su_menh': so_su_menh,
        'so_nhan_cach': so_nhan_cach, 'so_phat_trien': so_phat_trien,
        'so_truong_thanh': so_truong_thanh, 'so_noi_cam': so_noi_cam,
        'text_name': text_name, 'the_nhan_dang': the_nhan_dang, 'leak_num': leak_num,
        # ── New fields (report-gap G1-G6): arrows, isolated, karmic debt, compound ──
        **chart_fields,
    }
