"""Unit tests for the pure SVG chart engine (report_charts.py).

No DB / no async — drives the generators directly + via a real calc dict.
Asserts each function returns valid-ish SVG, handles edge inputs (all-zero,
master numbers, empty), and that build_charts wires calc → 4 charts.
"""

from app.core.numerology import calculate_numerology_numbers
from app.services.report_charts import (
    build_charts, core_radar_svg, cycle_wheel_svg, peaks_timeline_svg,
    power_bar_svg,
)

_DOB = "14071990"
_NAME = "Le Thi B"


class TestPowerBar:
    def test_returns_svg_with_all_digits(self):
        svg = power_bar_svg({str(d): d for d in range(1, 10)})
        assert svg.startswith("<svg") and svg.rstrip().endswith("</svg>")
        assert 'class="chart-svg chart-bar"' in svg

    def test_all_zero_counts_no_div_zero(self):
        svg = power_bar_svg({str(d): 0 for d in range(1, 10)})
        assert "<svg" in svg  # still renders the 9 digit labels + baseline

    def test_missing_keys_default_zero(self):
        svg = power_bar_svg({"1": 3})
        assert "<svg" in svg


class TestCoreRadar:
    def test_six_axes_render(self):
        vals = {
            "so_chu_dao": 7, "so_su_menh": 3, "so_linh_hon": 9,
            "so_nhan_cach": 1, "so_thai_do": 5, "so_truong_thanh": 8,
        }
        svg = core_radar_svg(vals)
        assert svg.startswith("<svg")
        assert "<polygon" in svg

    def test_master_number_capped_label_preserved(self):
        vals = {
            "so_chu_dao": 11, "so_su_menh": 22, "so_linh_hon": 33,
            "so_nhan_cach": 4, "so_thai_do": 5, "so_truong_thanh": 6,
        }
        svg = core_radar_svg(vals)
        # original master labels stay visible even though radius is capped to 1-9
        assert ">11<" in svg and ">22<" in svg

    def test_too_few_axes_returns_empty(self):
        assert core_radar_svg({"so_chu_dao": 7}) == ""


class TestPeaksTimeline:
    def test_four_nodes(self):
        peaks = [
            {"stage": i, "age_start": 20 + i, "peak": i, "challenge": i}
            for i in range(1, 5)
        ]
        svg = peaks_timeline_svg(peaks)
        assert svg.count("<circle") == 4

    def test_empty_returns_empty(self):
        assert peaks_timeline_svg([]) == ""


class TestCycleWheel:
    def test_nine_segments_and_highlight(self):
        svg = cycle_wheel_svg(3)
        assert svg.count("<path") == 9

    def test_out_of_range_year_clamped(self):
        # 22 → reduces to 4; should not raise and still produce 9 segments
        svg = cycle_wheel_svg(22)
        assert svg.count("<path") == 9


class TestBuildCharts:
    def test_all_four_from_real_calc(self):
        calc = calculate_numerology_numbers(_DOB, _NAME)
        charts = build_charts(calc, _DOB)
        assert set(charts) == {"power", "radar", "timeline", "wheel"}
        assert all(charts[k] and "<svg" in charts[k] for k in charts)

    def test_missing_calc_keys_safe(self):
        charts = build_charts({}, "")
        # power always renders (zero counts); others degrade to None, no crash
        assert charts["power"] and "<svg" in charts["power"]
        assert charts["radar"] is None
        assert charts["timeline"] is None
        assert charts["wheel"] is None
