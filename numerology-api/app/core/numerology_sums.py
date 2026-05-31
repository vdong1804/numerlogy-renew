"""Numerology digit-reduction helper functions.

Pure math — no I/O, no side effects. Split from numerology.py for ≤200 line rule.
"""


def get_sum(num: int) -> int:
    """Reduce to single digit 1-9, no master-number preservation."""
    tmp = sum(int(d) for d in str(num))
    if tmp > 9:
        return get_sum(tmp)
    return tmp


def get_sum_spec(num: int) -> int:
    """Reduce, preserving master numbers 11/22/33."""
    if int(num) in (11, 22, 33):
        return int(num)
    tmp = sum(int(d) for d in str(num))
    if tmp > 9:
        return get_sum_spec(tmp)
    return int(tmp)


def get_sum_new(num: int) -> int:
    """Like get_sum_spec — master-number aware; delegates to get_sum_spec for recursion."""
    if int(num) in (11, 22, 33):
        return int(num)
    tmp = sum(int(d) for d in str(num))
    if tmp > 9:
        return get_sum_spec(tmp)
    return int(tmp)


def get_sum_life(num: int) -> int:
    """Reduce preserving 10/11 (life-stage specific)."""
    if int(num) in (10, 11):
        return int(num)
    tmp = sum(int(d) for d in str(num))
    if tmp > 9:
        return get_sum_life(tmp)
    return int(tmp)
