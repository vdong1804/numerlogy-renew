"""Unit tests for alphabet and accent stripping."""

import pytest

from app.core.alphabet import alphabet, strip_accents


class TestStripAccents:
    """Vietnamese accent stripping."""

    def test_strip_grave_accents(self):
        """Strip grave accents (À, È, Ì, Ò, Ù, à, è, ì, ò, ù)."""
        assert strip_accents("À") == "A"
        assert strip_accents("Dào") == "Dao"
        assert strip_accents("à") == "a"

    def test_strip_acute_accents(self):
        """Strip acute accents (Á, É, Í, Ó, Ú, á, é, í, ó, ú)."""
        assert strip_accents("Á") == "A"
        assert strip_accents("Mái") == "Mai"

    def test_strip_circumflex_accents(self):
        """Strip circumflex (Â, Ê, Ô, â, ê, ô)."""
        assert strip_accents("Âu") == "Au"
        assert strip_accents("Tên") == "Ten"

    def test_strip_vietnamese_special(self):
        """Strip Vietnamese-specific marks (Ă, Đ, Ĩ, Ũ, Ơ, Ư)."""
        assert strip_accents("Ă") == "A"
        assert strip_accents("Đào") == "Dao"
        assert strip_accents("Ư") == "U"
        assert strip_accents("ở") == "o"

    def test_strip_combined_accents(self):
        """Strip multiple accents in one string."""
        assert strip_accents("ĐÀO THỊ MAI") == "DAO THI MAI"
        assert strip_accents("Nguyễn Văn A") == "Nguyen Van A"

    def test_plain_ascii_unchanged(self):
        """Plain ASCII should pass through unchanged."""
        assert strip_accents("Nguyen Van A") == "Nguyen Van A"
        assert strip_accents("ABC123") == "ABC123"

    def test_empty_string(self):
        """Empty string returns empty."""
        assert strip_accents("") == ""

    def test_mixed_accented_plain(self):
        """Mix of accented and plain text."""
        assert strip_accents("Tràng Định") == "Trang Dinh"


class TestAlphabetMapping:
    """Alphabet dict: letter → value + vowel flag."""

    def test_alphabet_has_26_letters(self):
        """Should map a-z."""
        assert len(alphabet) == 26

    def test_vowel_identification(self):
        """Vowels: a, e, i, o, u."""
        vowels = "aeiou"
        for v in vowels:
            assert alphabet[v]["is_vowel"] is True, f"{v} should be vowel"

    def test_consonant_identification(self):
        """Consonants: b, c, d, f, g, h, j, k, l, m, n, p, q, r, s, t, v, w, x, z."""
        consonants = "bcdfghjklmnpqrstvwxz"
        for c in consonants:
            assert alphabet[c]["is_vowel"] is False, f"{c} should be consonant"

    def test_value_range(self):
        """All letter values should be 1-9."""
        for letter, info in alphabet.items():
            assert 1 <= info["value"] <= 9, f"{letter} value out of range"

    def test_sample_values(self):
        """Sample letter values (from views.py const)."""
        assert alphabet["a"]["value"] == 1
        assert alphabet["b"]["value"] == 2
        assert alphabet["j"]["value"] == 1  # Repeats cycle
        assert alphabet["z"]["value"] == 8

    def test_dict_structure(self):
        """Each entry has 'value' and 'is_vowel' keys."""
        for letter, info in alphabet.items():
            assert "value" in info
            assert "is_vowel" in info
            assert isinstance(info["value"], int)
            assert isinstance(info["is_vowel"], bool)

    def test_case_sensitivity(self):
        """Alphabet is lowercase only."""
        for letter in alphabet.keys():
            assert letter.islower()
