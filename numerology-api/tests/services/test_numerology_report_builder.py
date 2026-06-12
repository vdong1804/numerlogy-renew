"""Structural tests for the numerology report builders (report-gap G1-G6).

Uses the empty SQLite test DB (no seeded content) — asserts the builders WIRE
the new indicators into the output (headings/keys flow through) even when
content rows are absent. Content correctness is covered by the seeded DB.
"""

import pytest

from app.core.numerology import calculate_numerology_numbers
from app.services.numerology_db import get_numerology_models
from app.services.numerology_full_report import build_report_view
from app.services.numerology_report_builder import build_report
from app.services.report_entitlement_service import ALL_SECTIONS, FREE_SECTIONS

# DOB born on the 14th + life-path total 13 → karmic debts 13 & 14.
_DOB = "14071990"
_NAME = "Le Thi B"


class TestFullReportView:
    async def test_personal_year_section_always_present(self, db_session):
        report = await build_report_view(db_session, _NAME, _DOB)
        headings = [s["heading"] for s in report["sections"]]
        assert any("SỐ NĂM CÁ NHÂN" in h for h in headings)

    async def test_karmic_debt_sections_when_present(self, db_session):
        report = await build_report_view(db_session, _NAME, _DOB)
        headings = [s["heading"] for s in report["sections"]]
        assert any("SỐ NỢ NGHIỆP 13/4" in h for h in headings)
        assert any("SỐ NỢ NGHIỆP 14/5" in h for h in headings)

    async def test_no_karmic_debt_no_section(self, db_session):
        # DOB with no karmic debt on any core → no nợ nghiệp section.
        report = await build_report_view(db_session, "An Binh", "02021992")
        if not report["calc"]["no_nghiep"]:
            headings = [s["heading"] for s in report["sections"]]
            assert not any("SỐ NỢ NGHIỆP" in h for h in headings)

    async def test_name_and_combined_charts_present(self, db_session):
        report = await build_report_view(db_session, _NAME, _DOB)
        assert len(report["chart_grid_name"]) == 3
        assert len(report["chart_grid_combined"]) == 3
        assert isinstance(report["name_chart_sections"], list)

    async def test_compound_heading_for_main_number(self, db_session):
        report = await build_report_view(db_session, _NAME, _DOB)
        assert report["sections"][0]["heading"].startswith("SỐ CHỦ ĐẠO ")


class TestJsonReportBuilder:
    async def test_new_keys_present(self, db_session):
        calc = calculate_numerology_numbers(_DOB, _NAME)
        models = await get_numerology_models(db_session, calc)
        rep = build_report(_NAME, _DOB, calc, models, ALL_SECTIONS)
        assert "compound" in rep["so_chu_dao"]
        assert "nam_ca_nhan" in rep["personal"]
        assert "karmic_debt" in rep
        assert "name_chart" in rep
        assert "arrows" in rep
        assert "combined" in rep["power_chart"]

    async def test_arrows_shape(self, db_session):
        calc = calculate_numerology_numbers(_DOB, _NAME)
        models = await get_numerology_models(db_session, calc)
        rep = build_report(_NAME, _DOB, calc, models, ALL_SECTIONS)
        arrows = rep["arrows"]
        assert set(arrows) == {"present", "empty", "isolated"}


class TestReportGating:
    """Free tier must strip locked content; paid tier keeps it."""

    async def _build(self, db_session, unlocked):
        calc = calculate_numerology_numbers(_DOB, _NAME)
        models = await get_numerology_models(db_session, calc)
        return build_report(_NAME, _DOB, calc, models, unlocked)

    async def test_free_locks_core_numbers(self, db_session):
        rep = await self._build(db_session, FREE_SECTIONS)
        # su_menh is NOT in FREE_SECTIONS → must be locked + content stripped.
        su_menh = rep["core_numbers"]["su_menh"]
        assert su_menh["locked"] is True
        assert su_menh["content"] is None

    async def test_free_keeps_unlocked_sections_unmarked(self, db_session):
        rep = await self._build(db_session, FREE_SECTIONS)
        # so_chu_dao IS free → main not locked (content present if DB seeded).
        assert "locked" not in rep["so_chu_dao"]
        # so_chu_dao_extra is NOT free → extra facets nulled + flagged.
        assert rep["so_chu_dao"]["content_2"] is None
        assert rep["so_chu_dao"]["extra_locked"] is True

    async def test_free_strips_peaks_and_challenges(self, db_session):
        rep = await self._build(db_session, FREE_SECTIONS)
        assert all(p["locked"] is True and p["content"] is None for p in rep["peaks"])
        assert all(c["locked"] is True and c["content"] is None for c in rep["challenges"])

    async def test_paid_unlocks_everything(self, db_session):
        rep = await self._build(db_session, ALL_SECTIONS)
        assert "locked" not in rep["core_numbers"]["su_menh"]
        assert all("locked" not in p for p in rep["peaks"])
