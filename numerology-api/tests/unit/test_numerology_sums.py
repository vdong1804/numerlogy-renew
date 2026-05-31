"""Unit tests for numerology sum reduction functions."""

import pytest

from app.core.numerology_sums import get_sum, get_sum_spec, get_sum_new, get_sum_life


class TestGetSum:
    """get_sum: reduce to 1-9, no master-number preservation."""

    def test_single_digit(self):
        """Single digit 1-9 returns unchanged."""
        for n in range(1, 10):
            assert get_sum(n) == n

    def test_two_digit_reduction(self):
        """Two-digit reduces: 10→1, 11→2, 15→6."""
        assert get_sum(10) == 1
        assert get_sum(11) == 2
        assert get_sum(15) == 6
        assert get_sum(18) == 9

    def test_master_numbers_not_preserved(self):
        """Master 11, 22, 33 reduce: 11→2, 22→4, 33→6."""
        assert get_sum(11) == 2
        assert get_sum(22) == 4
        assert get_sum(33) == 6

    def test_large_number_reduction(self):
        """Recursive reduction: 999 → 27 → 9."""
        assert get_sum(999) == 9
        assert get_sum(123) == 6

    def test_zero_input(self):
        """Zero reduces to 0."""
        assert get_sum(0) == 0


class TestGetSumSpec:
    """get_sum_spec: reduce preserving master 11, 22, 33."""

    def test_single_digit(self):
        """1-9 unchanged."""
        for n in range(1, 10):
            assert get_sum_spec(n) == n

    def test_master_numbers_preserved(self):
        """11, 22, 33 preserved."""
        assert get_sum_spec(11) == 11
        assert get_sum_spec(22) == 22
        assert get_sum_spec(33) == 33

    def test_non_master_two_digit_reduction(self):
        """Non-master two-digit reduces: 12→3, 15→6, 29→11."""
        assert get_sum_spec(12) == 3
        assert get_sum_spec(15) == 6
        assert get_sum_spec(29) == 11  # 2+9=11, preserved

    def test_large_number_to_master(self):
        """Large number reducing to master: 29→11 (preserved), 38→11."""
        assert get_sum_spec(29) == 11
        assert get_sum_spec(38) == 11
        assert get_sum_spec(47) == 11

    def test_large_number_non_master(self):
        """Large number reducing to 1-9: 123→6."""
        assert get_sum_spec(123) == 6
        assert get_sum_spec(999) == 9

    def test_zero_input(self):
        """Zero → 0."""
        assert get_sum_spec(0) == 0

    def test_40_to_4(self):
        """40 → 4 (not master)."""
        assert get_sum_spec(40) == 4


class TestGetSumNew:
    """get_sum_new: like get_sum_spec (master-aware)."""

    def test_master_numbers_preserved(self):
        """11, 22, 33 preserved."""
        assert get_sum_new(11) == 11
        assert get_sum_new(22) == 22
        assert get_sum_new(33) == 33

    def test_single_digit(self):
        """1-9 unchanged."""
        for n in range(1, 10):
            assert get_sum_new(n) == n

    def test_non_master_two_digit(self):
        """Non-master two-digit reduces: 12→3, 15→6."""
        assert get_sum_new(12) == 3
        assert get_sum_new(15) == 6

    def test_large_number_to_master(self):
        """Large number → master: 29→11."""
        assert get_sum_new(29) == 11

    def test_delegates_to_spec(self):
        """get_sum_new should match get_sum_spec."""
        test_values = [0, 5, 10, 11, 15, 22, 29, 33, 100, 123]
        for val in test_values:
            assert get_sum_new(val) == get_sum_spec(val)


class TestGetSumLife:
    """get_sum_life: reduce preserving 10, 11 (life-stage specific)."""

    def test_single_digit(self):
        """1-9 unchanged."""
        for n in range(1, 10):
            assert get_sum_life(n) == n

    def test_10_preserved(self):
        """10 preserved (not in other functions)."""
        assert get_sum_life(10) == 10

    def test_11_preserved(self):
        """11 preserved."""
        assert get_sum_life(11) == 11

    def test_non_preserved_master_22_reduces(self):
        """22 reduces to 4."""
        assert get_sum_life(22) == 4

    def test_non_preserved_master_33_reduces(self):
        """33 reduces to 6."""
        assert get_sum_life(33) == 6

    def test_two_digit_reduction(self):
        """Non-10/11 two-digit reduces: 12→3, 15→6."""
        assert get_sum_life(12) == 3
        assert get_sum_life(15) == 6

    def test_large_number_to_preserved(self):
        """Large number → 10: 19→10 (1+9=10)."""
        assert get_sum_life(19) == 10

    def test_large_number_non_preserved(self):
        """Large number → non-preserved: 123→6."""
        assert get_sum_life(123) == 6

    def test_zero_input(self):
        """0 → 0."""
        assert get_sum_life(0) == 0


class TestEdgeCases:
    """Cross-function edge cases."""

    def test_zero_consistency(self):
        """All functions handle 0."""
        assert get_sum(0) == 0
        assert get_sum_spec(0) == 0
        assert get_sum_new(0) == 0
        assert get_sum_life(0) == 0

    def test_consistency_on_1_to_9(self):
        """All functions agree on 1-9."""
        for n in range(1, 10):
            assert get_sum(n) == n
            assert get_sum_spec(n) == n
            assert get_sum_new(n) == n
            assert get_sum_life(n) == n

    def test_consistency_on_non_master_10(self):
        """get_sum_life preserves 10, others reduce."""
        assert get_sum(10) == 1
        assert get_sum_spec(10) == 1
        assert get_sum_new(10) == 1
        assert get_sum_life(10) == 10

    def test_consistency_on_master_11(self):
        """All except get_sum preserve 11."""
        assert get_sum(11) == 2
        assert get_sum_spec(11) == 11
        assert get_sum_new(11) == 11
        assert get_sum_life(11) == 11

    def test_consistency_on_master_22(self):
        """get_sum_spec and get_sum_new preserve 22; others reduce."""
        assert get_sum(22) == 4
        assert get_sum_spec(22) == 22
        assert get_sum_new(22) == 22
        assert get_sum_life(22) == 4
