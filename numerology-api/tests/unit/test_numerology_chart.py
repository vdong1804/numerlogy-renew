"""Unit tests for app.core.numerology_chart (pure, no DB).

Covers the birth-chart derivations added for the report-gap work:
arrows (strength/empty), isolated corners, karmic-debt detection, compound display.
"""

from app.core.numerology_chart import (
    compound_str, compute_arrows, compute_isolated, derive_chart_fields,
    detect_karmic_debt,
)


class TestComputeArrows:
    def test_full_physical_line_is_strength(self):
        # digits 1,4,7 all present → strength arrow "147"
        strength, _ = compute_arrows({"1", "4", "7"})
        assert "147" in strength

    def test_absent_line_is_empty_arrow(self):
        # only 7,8,9 present → 1-2-3 and 4-5-6 fully absent → empty arrows
        strength, empty = compute_arrows({"7", "8", "9"})
        assert "789" in strength
        assert "not_123" in empty
        assert "not_456" in empty

    def test_partial_line_is_neither(self):
        # 1,4 present but 7 missing → 147 neither strength nor empty
        strength, empty = compute_arrows({"1", "4"})
        assert "147" not in strength
        assert "not_147" not in empty


class TestComputeIsolated:
    def test_one_isolated_when_neighbours_absent(self):
        # 1 present, neighbours 2/4/5 absent → isolated
        assert compute_isolated({"1", "9"}) == [1] or 1 in compute_isolated({"1", "9"})

    def test_one_not_isolated_when_neighbour_present(self):
        # 1 present but 4 present → not isolated
        assert 1 not in compute_isolated({"1", "4"})

    def test_only_corner_numbers_considered(self):
        # 5 is centre, never isolated
        assert compute_isolated({"5"}) == []


class TestDetectKarmicDebt:
    def test_two_digit_karmic_values(self):
        assert detect_karmic_debt(13) == 13
        assert detect_karmic_debt(14) == 14
        assert detect_karmic_debt(16) == 16
        assert detect_karmic_debt(19) == 19

    def test_non_karmic_two_digit(self):
        assert detect_karmic_debt(22) is None
        assert detect_karmic_debt(12) is None

    def test_single_digit_is_none(self):
        assert detect_karmic_debt(4) is None

    def test_reduction_path_through_karmic(self):
        # 49 → 13 → 4 : passes through 13
        assert detect_karmic_debt(49) == 13


class TestCompoundStr:
    def test_two_digit_compound(self):
        assert compound_str(13) == "13/4"
        assert compound_str(22) == "22/4"

    def test_single_digit_stays_single(self):
        assert compound_str(6) == "6"

    def test_large_total_shows_penultimate(self):
        # 49 → 13 → 4 : display penultimate 13/4
        assert compound_str(49) == "13/4"


class TestDeriveChartFields:
    def test_bundle_keys_present(self):
        fields = derive_chart_fields(
            birth_day="14071990", text_name="345",
            chu_dao_total=13, sum_full_name=12,
            sum_full_vowel=5, sum_full_consonant=7,
        )
        for key in (
            "arrows_present", "arrows_empty", "isolated",
            "name_counts", "no_nghiep", "so_chu_dao_compound",
        ):
            assert key in fields

    def test_karmic_debt_sorted_and_deduped(self):
        # chu_dao_total 13 + day-of-month 14 → [13, 14]
        fields = derive_chart_fields(
            birth_day="14071990", text_name="",
            chu_dao_total=13, sum_full_name=1,
            sum_full_vowel=1, sum_full_consonant=1,
        )
        assert fields["no_nghiep"] == [13, 14]
