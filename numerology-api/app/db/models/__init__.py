"""Model registry — import all modules so Alembic autogenerate sees every table."""

from app.db.models.numerology_content import *  # noqa: F401, F403
from app.db.models.user import *  # noqa: F401, F403
from app.db.models.auth import *  # noqa: F401, F403
from app.db.models.download import *  # noqa: F401, F403
from app.db.models.package import *  # noqa: F401, F403
from app.db.models.news import *  # noqa: F401, F403
from app.db.models.product import *  # noqa: F401, F403
from app.db.models.order import *  # noqa: F401, F403
from app.db.models.user_report import *  # noqa: F401, F403
from app.db.models.webhook_event import *  # noqa: F401, F403
from app.db.models.email_outbox import *  # noqa: F401, F403
from app.db.models.chat import *  # noqa: F401, F403

# Re-export Base so callers can do: from app.db import models; models.Base.metadata
from app.db.base import Base  # noqa: F401
