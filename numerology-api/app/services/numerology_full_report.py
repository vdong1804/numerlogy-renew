"""Build the full personalized numerology report view (SAMPLE-style).

Single source of truth for the long-form report: assembles header info, the
Pythagoras birth chart grid, and an ordered list of interpretation sections
(numbers computed by the algorithm, content rows fetched from DB).

Consumed by:
  - invoice.html (web/PDF report) via routers
  - scripts/build_report_payload.py (offline docx export)
"""

from __future__ import annotations

from collections import Counter

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.numerology import calculate_numerology_numbers, get_sum
from app.services.report_charts import build_charts
from app.db.models.numerology_content import (
    AttitudeNumber, BirthdayChart, BirthdayNumber, ChallengeLife,
    DevelopmentNumber, GrowthNumber, Identifiable, KarmicDebtNumber,
    KarmicNumber, LifePeak, MainNumber, MatureNumber, MissNumber,
    MissionNumber, NameChart, PersonalMonthNumber, PersonalYearNumber,
    PhoneNumber, SoulsNumber, StagesOfLife,
)
from app.services.numerology_db import fetch_by_code
from app.services.report_assets import archetype_image, cover_fallback

# Pythagoras chart fixed layout (top→bottom rows)
_CHART_LAYOUT = [["3", "6", "9"], ["2", "5", "8"], ["1", "4", "7"]]


async def build_report_view(
    db: AsyncSession, full_name: str, birth_day: str, phone: str = "",
) -> dict:
    """Compute numbers + fetch content → structured report dict.

    Raises ValueError (from calc) if the name has no mappable characters.
    """
    calc = calculate_numerology_numbers(birth_day, full_name)
    sections: list[dict] = []

    async def row(model, code):
        return await fetch_by_code(db, model, code)

    async def add(heading: str, model, code):
        r = await row(model, code)
        sections.append({
            "heading": heading,
            "title": r.title if r else "",
            "content": r.content if r else "",
        })

    # 1. Số chủ đạo (+ MainNumber extra facets content_2..5)
    main = await row(MainNumber, calc["so_chu_dao"])
    main_html = (main.content if main else "")
    if main:
        for extra in (main.content_2, main.content_3, main.content_4, main.content_5):
            if extra:
                main_html += extra
    sections.append({
        "heading": f"SỐ CHỦ ĐẠO {calc['so_chu_dao_compound']}",
        "title": main.title if main else "", "content": main_html,
    })

    # 2. Birth chart grid + present-digit interpretations
    present = {str(d): birth_day.count(str(d)) for d in range(1, 10)}
    chart_grid = [[(d * present[d]) for d in r] for r in _CHART_LAYOUT]
    chart_sections: list[dict] = []
    for d in sorted(c for c in present if present[c]):
        base = await row(BirthdayChart, d)
        sub = await row(BirthdayChart, f"{d}_{present[d]}")
        html = (base.content if base else "") + (sub.content if sub else "")
        chart_sections.append({
            "heading": f"Số {d} trong biểu đồ ngày sinh (×{present[d]})",
            "content": html,
        })

    # 2b. Mũi tên (mạnh/trống) + số lẻ loi (G4/G5) — nối vào chart_sections
    for code in calc["arrows_present"]:
        r = await row(BirthdayChart, code)
        if r:
            chart_sections.append({"heading": r.title or f"Mũi tên {code}", "content": r.content})
    for code in calc["arrows_empty"]:  # code đã có tiền tố not_
        r = await row(BirthdayChart, code)
        if r:
            chart_sections.append({"heading": r.title or f"Mũi tên trống {code}", "content": r.content})
    for d in calc["isolated"]:
        r = await row(BirthdayChart, f"{d}_single")
        if r:
            chart_sections.append({"heading": r.title or f"Số {d} lẻ loi", "content": r.content})

    # 2c. Biểu đồ Tên + Tổng hợp (G3) — ô = chữ số lặp theo số lần xuất hiện
    # (cùng quy ước string-repeat với chart_grid, vd "33" = số 3 xuất hiện 2 lần).
    name_counts = calc["name_counts"]
    chart_grid_name = [[d * name_counts[d] for d in r] for r in _CHART_LAYOUT]
    chart_grid_combined = [
        [d * (present[d] + name_counts[d]) for d in r] for r in _CHART_LAYOUT
    ]
    name_chart_sections: list[dict] = []
    for d in sorted(c for c in name_counts if name_counts[c]):
        nr = await row(NameChart, d)
        name_chart_sections.append({
            "heading": f"Số {d} trong biểu đồ tên (×{name_counts[d]})",
            "content": nr.content if nr else "",
        })

    # 3. Ba giai đoạn
    for i in (1, 2, 3):
        await add(f"GIAI ĐOẠN CUỘC ĐỜI {i}", StagesOfLife, i)

    # 4. Bốn đỉnh cao + thử thách
    for i in range(1, 5):
        peak, chal, age = calc[f"dinh_cao_{i}"], calc[f"thu_thach_{i}"], calc[f"tuoi_dinh_cao_{i}"]
        pr = await row(LifePeak, peak)
        cr = await row(ChallengeLife, chal)
        html = (pr.content if pr else "")
        if cr:
            html += f"<h4>Thử thách số {chal}</h4>{cr.content}"
        sections.append({
            "heading": f"ĐỈNH CAO {i} — SỐ {peak} (≈ tuổi {age}), THỬ THÁCH {chal}",
            "title": pr.title if pr else "", "content": html,
        })

    # 5. Các chỉ số cốt lõi (thứ tự theo SAMPLE)
    await add(f"SỐ THÁI ĐỘ {calc['so_thai_do']}", AttitudeNumber, calc["so_thai_do"])
    await add(f"SỐ NGÀY SINH {calc['so_ngay_sinh']}", BirthdayNumber, calc["so_ngay_sinh"])
    await add(f"SỐ SỨ MỆNH {calc['so_su_menh']}", MissionNumber, calc["so_su_menh"])
    await add(f"SỐ LINH HỒN {calc['so_linh_hon']}", SoulsNumber, calc["so_linh_hon"])
    await add(f"SỐ NHÂN CÁCH {calc['so_nhan_cach']}", MatureNumber, calc["so_nhan_cach"])
    await add(f"SỐ TRƯỞNG THÀNH {calc['so_truong_thanh']}", DevelopmentNumber, calc["so_truong_thanh"])
    await add(f"SỐ PHÁT TRIỂN {calc['so_phat_trien']}", GrowthNumber, calc["so_phat_trien"])
    await add(f"SỐ NỘI CẢM {calc['so_noi_cam']}", KarmicNumber, calc["so_noi_cam"])
    # Số Nợ Nghiệp (G1) — chỉ render khi có; hiển thị dạng kép code/single
    for code in calc["no_nghiep"]:
        await add(f"SỐ NỢ NGHIỆP {code}/{get_sum(code)}", KarmicDebtNumber, code)
    for miss in calc["leak_num"]:
        await add(f"SỐ THIẾU {miss}", MissNumber, miss)
    await add(f"THỂ NHÂN DẠNG {calc['the_nhan_dang']}", Identifiable, calc["the_nhan_dang"])
    phone_code = get_sum(sum(int(c) for c in phone if c.isdigit())) if phone else 0
    if phone_code:
        await add(f"SỐ ĐIỆN THOẠI {phone_code}", PhoneNumber, phone_code)
    await add(f"SỐ NĂM CÁ NHÂN {calc['so_nam_ca_nhan']}", PersonalYearNumber, calc["so_nam_ca_nhan"])
    await add(f"SỐ THÁNG CÁ NHÂN {calc['so_thang_ca_nhan']}", PersonalMonthNumber, calc["so_thang_ca_nhan"])

    summary = [
        ("Số chủ đạo", calc["so_chu_dao_compound"]), ("Số thái độ", calc["so_thai_do"]),
        ("Số sứ mệnh", calc["so_su_menh"]), ("Số linh hồn", calc["so_linh_hon"]),
        ("Số nhân cách", calc["so_nhan_cach"]), ("Số trưởng thành", calc["so_truong_thanh"]),
        ("Số phát triển", calc["so_phat_trien"]), ("Số nội cảm", calc["so_noi_cam"]),
        ("Số nợ nghiệp", ", ".join(f"{c}/{get_sum(c)}" for c in calc["no_nghiep"]) or "—"),
        ("Thể nhân dạng", calc["the_nhan_dang"]),
        ("Số năm cá nhân", calc["so_nam_ca_nhan"]),
        ("Số tháng cá nhân", calc["so_thang_ca_nhan"]),
        ("Số thiếu", ", ".join(map(str, calc["leak_num"])) or "—"),
    ]

    return {
        "header": {
            "name": full_name.upper(),
            "birth_day_text": f"{birth_day[:2]}/{birth_day[2:4]}/{birth_day[4:]}",
            "phone": phone,
        },
        # Static illustrations (P3). cover_bg = default art; P4 overrides per-user.
        "archetype_image": archetype_image(calc["so_chu_dao"]),
        "cover_bg": cover_fallback(),
        "summary": summary,
        "chart_grid": chart_grid,
        "chart_sections": chart_sections,
        "chart_grid_name": chart_grid_name,
        "chart_grid_combined": chart_grid_combined,
        "name_chart_sections": name_chart_sections,
        "sections": sections,
        "calc": calc,
        # 4 cosmic charts (power/radar/timeline/wheel) for the PDF report.
        "charts": build_charts(calc, birth_day),
    }
