"""Unit tests for ref_code generation utility."""

import re

import pytest

from app.utils.ref_code import generate_ref_code

REF_CODE_RE = re.compile(r"^NSQ-[23456789ABCDEFGHJKMNPQRSTVWXYZ]{8}$")


def test_format_matches_strict_pattern():
    code = generate_ref_code()
    assert REF_CODE_RE.match(code), f"Unexpected format: {code}"


@pytest.mark.parametrize("ambiguous", ["0", "O", "1", "I", "L", "U"])
def test_ambiguous_characters_excluded(ambiguous):
    """Codes should never contain easily-confused characters."""
    samples = {generate_ref_code()[4:] for _ in range(2000)}  # strip NSQ- prefix
    combined = "".join(samples)
    assert ambiguous not in combined, f"Ambiguous char '{ambiguous}' leaked into output"


def test_low_collision_rate_over_10000_iterations():
    codes = {generate_ref_code() for _ in range(10000)}
    # With 28^8 (~3.7 * 10^11) possible codes, collisions in 10k should be 0
    assert len(codes) == 10000
