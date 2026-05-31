"""Numerology service — re-export facade for backward compatibility.

Actual implementation split across:
  app/services/numerology_db.py     — DB query helpers
  app/services/numerology_context.py — context builder + save/decrement
"""

from app.services.numerology_db import (  # noqa: F401
    fetch_by_code,
    fetch_many_by_codes,
    get_free_extra_models,
    get_numerology_models,
)
from app.services.numerology_context import (  # noqa: F401
    build_common_context,
    decrement_quota,
    save_user_download,
)
