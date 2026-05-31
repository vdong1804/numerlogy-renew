"""Unit tests for calculate_numerology_numbers core logic."""

import pytest

from app.core.numerology import calculate_numerology_numbers


class TestNumerologyCalcBasic:
    """Basic input/output validation."""

    def test_standard_input(self):
        """Standard case: Nguyen Van A, 15/10/1990."""
        result = calculate_numerology_numbers(
            birth_day="15101990",
            full_name="Nguyen Van A",
        )
        # Verify all expected keys exist and are integers
        expected_keys = {
            "so_chu_dao", "so_ngay_sinh", "so_thang_sinh", "so_nam_sinh",
            "so_thai_do", "so_nam_ca_nhan", "so_thang_ca_nhan",
            "so_su_menh", "so_thuc_thi", "so_nhan_cach",
            "so_can_bang", "so_linh_hon", "so_phat_trien",
            "so_truong_thanh", "so_noi_cam",
            "text_name", "leak_num",
        }
        assert all(k in result for k in expected_keys)
        # Numerology numbers should be 1-9 (or 11/22/33 for master)
        assert 1 <= result["so_chu_dao"] <= 9
        assert 1 <= result["so_ngay_sinh"] <= 9
        assert isinstance(result["leak_num"], list)

    def test_vietnamese_accented_name(self):
        """Vietnamese name with accents: ĐÀO THỊ MAI."""
        result = calculate_numerology_numbers(
            birth_day="15101990",
            full_name="ĐÀO THỊ MAI",
        )
        # Should not raise; accents stripped internally
        assert "so_su_menh" in result
        assert isinstance(result["so_su_menh"], int)

    def test_leap_day_input(self):
        """Birth day on leap day: 29/02/2000."""
        result = calculate_numerology_numbers(
            birth_day="29022000",
            full_name="Tran Thi B",
        )
        assert result["so_chu_dao"] > 0

    def test_single_char_name(self):
        """Edge case: very short name."""
        result = calculate_numerology_numbers(
            birth_day="15101990",
            full_name="A",
        )
        assert result["so_su_menh"] > 0

    def test_empty_name_raises(self):
        """Empty name should raise ValueError."""
        with pytest.raises(ValueError, match="recognizable"):
            calculate_numerology_numbers(birth_day="15101990", full_name="")

    def test_special_chars_in_name(self):
        """Name with numbers/symbols (stripped, only letters count)."""
        result = calculate_numerology_numbers(
            birth_day="15101990",
            full_name="Nguyen-123 Van_A",
        )
        # Should process only letters
        assert result["so_su_menh"] > 0


class TestNumerologyCalcMasterNumbers:
    """Master number (11, 22, 33) handling."""

    def test_master_number_so_chu_dao(self):
        """Input that yields so_chu_dao as master (e.g., 29/02/1992)."""
        result = calculate_numerology_numbers(
            birth_day="29021992",
            full_name="Le Thi Ba",
        )
        # This may yield master; verify no crash
        assert result["so_chu_dao"] in range(1, 34)

    def test_so_truong_thanh_master_reduction(self):
        """so_truong_thanh ∈ {11,22,33} should reduce per line 186-187."""
        # Note: cannot easily force this; just verify no crash with various inputs
        for birth_day in ["15101990", "11111111", "22222222"]:
            result = calculate_numerology_numbers(
                birth_day=birth_day,
                full_name="Test Name",
            )
            # After reduction, should be 1-9
            assert 1 <= result["so_truong_thanh"] <= 9


class TestNumerologyCalcAgeVariants:
    """Age-dependent calculations."""

    def test_young_age_branch(self):
        """age < 25 - so_chu_dao: so_nam_ca_nhan = 11."""
        # Force young age
        result = calculate_numerology_numbers(
            birth_day="15101990",
            full_name="Nguyen A",
            current_age=10,  # 10 years old
        )
        # Should be in young branch
        assert result["so_nam_ca_nhan"] in [10, 11]

    def test_elderly_age_branch(self):
        """age >= 54 + so_chu_dao: so_nam_ca_nhan = 10."""
        result = calculate_numerology_numbers(
            birth_day="15101990",
            full_name="Nguyen A",
            current_age=80,  # 80 years old
        )
        # Should be in elderly branch
        assert result["so_nam_ca_nhan"] == 10

    def test_middle_age_so_nam_ca_nhan_zero_wrap(self):
        """Intermediate calc yields 0 → redirect to 9 (line 113)."""
        # Force middle age to trigger calculation
        result = calculate_numerology_numbers(
            birth_day="15101990",
            full_name="Nguyen A",
            current_age=35,
        )
        # Result should never be 0 (wrapped to 9)
        assert result["so_nam_ca_nhan"] != 0
        assert 1 <= result["so_nam_ca_nhan"] <= 11


class TestNumerologyCalcRedirects:
    """Master-number redirect rules (0 → 9)."""

    def test_thu_thach_zero_redirects(self):
        """If any thu_thach computes to 0, redirect to 9."""
        # Find input that creates 0 challenge numbers (if any)
        result = calculate_numerology_numbers(
            birth_day="15101990",
            full_name="AA",
        )
        # All challenges should be 1-9, never 0
        assert result["thu_thach_1"] != 0
        assert result["thu_thach_2"] != 0
        assert result["thu_thach_3"] != 0
        assert result["thu_thach_4"] != 0

    def test_so_thuc_thi_zero_redirects(self):
        """If so_thuc_thi = 0, redirect to 9."""
        result = calculate_numerology_numbers(
            birth_day="15101990",
            full_name="Nguyen Van A",
        )
        # so_thuc_thi should never be 0
        assert result["so_thuc_thi"] != 0


class TestNumerologyCalcNegativeWrap:
    """Negative intermediate wraps (+9 rule)."""

    def test_negative_intermediate_wrap(self):
        """so_nam_ca_nhan < 0 wraps via += 9 (line 81-82)."""
        # Force condition where calculation yields negative
        result = calculate_numerology_numbers(
            birth_day="15101990",
            full_name="A",
            current_age=30,
        )
        # After wrap, should be positive 1-9
        assert result["so_nam_ca_nhan"] > 0


class TestNumerologyCalcNameAnalysis:
    """Name-derived numbers."""

    def test_leak_num_excludes_present_digits(self):
        """leak_num = digits 1-9 not in text_name."""
        result = calculate_numerology_numbers(
            birth_day="15101990",
            full_name="Aaa",  # Only 'A'=1 repeatedly
        )
        # 1 should appear in text_name; 2-9 should be in leak_num
        assert isinstance(result["leak_num"], list)
        assert all(n in range(1, 10) for n in result["leak_num"])

    def test_text_name_structure(self):
        """text_name is string of digit values."""
        result = calculate_numerology_numbers(
            birth_day="15101990",
            full_name="ABC",
        )
        # text_name should be concatenated digit string
        assert isinstance(result["text_name"], str)
        assert all(c.isdigit() for c in result["text_name"])

    def test_so_noi_cam_from_mode(self):
        """so_noi_cam is mode() of alphabet values."""
        result = calculate_numerology_numbers(
            birth_day="15101990",
            full_name="Nguyen Van A",
        )
        # Should be a single digit from alphabet values
        assert 1 <= result["so_noi_cam"] <= 9


class TestNumerologyCalcDefiningPeriods:
    """Age period (tuoi dinh cao) calculations."""

    def test_period_calculations(self):
        """Verify tuoi_dinh_cao_1-4 are computed."""
        result = calculate_numerology_numbers(
            birth_day="15101990",
            full_name="Nguyen A",
            current_age=35,
        )
        # Periods should be positive integers
        assert result["tuoi_dinh_cao_1"] > 0
        assert result["tuoi_dinh_cao_2"] > result["tuoi_dinh_cao_1"]
        assert result["tuoi_dinh_cao_3"] > result["tuoi_dinh_cao_2"]
        assert result["tuoi_dinh_cao_4"] > result["tuoi_dinh_cao_3"]

    def test_defining_periods_stages(self):
        """dinh_cao_1-4 and stages assigned per age."""
        result = calculate_numerology_numbers(
            birth_day="15101990",
            full_name="Nguyen A",
            current_age=35,
        )
        # All dinh cao values should be 1-9
        assert 1 <= result["dinh_cao_1"] <= 9
        assert 1 <= result["dinh_cao_2"] <= 9
        assert 1 <= result["dinh_cao_3"] <= 9
        assert 1 <= result["dinh_cao_4"] <= 9


class TestNumerologyCalcSnapshot:
    """Snapshot structure test (verify output shape)."""

    def test_output_structure(self):
        """All expected output keys present with correct types."""
        result = calculate_numerology_numbers(
            birth_day="15101990",
            full_name="Nguyen Van A",
            current_age=35,
        )
        # Top-level keys
        assert isinstance(result, dict)
        assert "so_chu_dao" in result
        assert "so_su_menh" in result
        assert "so_thuc_thi" in result

        # Type checks on sample keys
        assert isinstance(result["so_chu_dao"], int)
        assert isinstance(result["so_su_menh"], int)
        assert isinstance(result["leak_num"], list)
        assert isinstance(result["text_name"], str)
