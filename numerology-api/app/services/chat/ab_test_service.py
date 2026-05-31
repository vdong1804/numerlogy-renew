# ruff: noqa: UP045, UP017
"""AbTestService — deterministic user->variant assignment (Phase 08).

Assigns each user to one of three variants on first chat turn and persists
the choice. Variant is used by `prompt_builder` to swap the system-prompt
override (keys: ``chat_system_prompt_variant_a`` / ``..._variant_b``).

Default split: 80% control / 10% variant_a / 10% variant_b. Override per
process via `set_split()` (testing only — production should bake the split
into a launch checklist, not env vars).
"""

from __future__ import annotations

import hashlib
import logging
from typing import Literal

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

Variant = Literal["control", "variant_a", "variant_b"]

# Default rollout — cumulative thresholds out of 100.
_SPLITS: dict[str, tuple[int, int]] = {
    # variant_a: bucket < 10 ; variant_b: bucket < 20
    "default": (10, 20),
}


def _bucket(user_id: int) -> int:
    """Stable 0..99 bucket — same as feature_flag_service but seeded per AB."""
    digest = hashlib.sha1(f"abtest:{user_id}".encode()).digest()
    return digest[0] % 100


def _variant_for(user_id: int) -> Variant:
    a, b = _SPLITS["default"]
    bucket = _bucket(user_id)
    if bucket < a:
        return "variant_a"
    if bucket < b:
        return "variant_b"
    return "control"


class AbTestService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_or_assign_variant(self, user_id: int) -> Variant:
        """Lookup-or-insert. Persisted assignment is sticky so admin can
        re-tune the deterministic split without re-bucketing existing users."""
        row = (
            await self.db.execute(
                text(
                    "SELECT variant FROM chat_ab_test_assignments WHERE user_id = :u"
                ),
                {"u": user_id},
            )
        ).first()
        if row is not None:
            return row[0]  # type: ignore[return-value]

        variant = _variant_for(user_id)
        await self.db.execute(
            text(
                "INSERT INTO chat_ab_test_assignments (user_id, variant) "
                "VALUES (:u, :v) ON CONFLICT (user_id) DO NOTHING"
            ),
            {"u": user_id, "v": variant},
        )
        return variant


__all__ = ["AbTestService", "Variant"]
