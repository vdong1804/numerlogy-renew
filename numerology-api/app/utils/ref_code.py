"""Generate human-readable order reference codes (NSQ-XXXXXXXX).

Uses Crockford base32 alphabet (excludes 0/O, 1/I/L, U) so codes are
safe to copy / read aloud / type into a SePay description field.

8 chars from a 28-char alphabet => ~3.7 * 10^11 combinations.
With UNIQUE(ref_code) constraint, we retry on the rare collision.
"""

import secrets

# Crockford-style alphabet, removed ambiguous chars: 0 O I L 1 U
_ALPHABET = "23456789ABCDEFGHJKMNPQRSTVWXYZ"
_PREFIX = "NSQ-"
_CODE_LEN = 8


def generate_ref_code() -> str:
    """Return a fresh code like ``NSQ-A2K7XJ9R``.

    Caller is responsible for retry-on-collision against the UNIQUE constraint.
    """
    code = "".join(secrets.choice(_ALPHABET) for _ in range(_CODE_LEN))
    return f"{_PREFIX}{code}"
