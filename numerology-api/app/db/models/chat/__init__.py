"""Chat + KB ORM models — registered for Alembic autogenerate."""

from app.db.models.chat.ab_test_assignment import ChatAbTestAssignment
from app.db.models.chat.abuse_flag import ChatAbuseFlag
from app.db.models.chat.chat_addon_purchase import ChatAddonPurchase
from app.db.models.chat.conversation import ChatConversation
from app.db.models.chat.daily_metrics import ChatDailyMetrics
from app.db.models.chat.feature_flag import ChatFeatureFlag
from app.db.models.chat.kb_chunk import KbChunk
from app.db.models.chat.kb_document import KbDocument
from app.db.models.chat.message import ChatMessage
from app.db.models.chat.quota_usage import ChatQuotaUsage
from app.db.models.chat.rate_limit_bucket import RateLimitBucket
from app.db.models.chat.semantic_cache_entry import SemanticCacheEntry
from app.db.models.chat.system_settings import (
    ChatSystemSetting,
    ChatSystemSettingHistory,
)
from app.db.models.chat.user_pdf_chunk import UserPdfChunk
from app.db.models.chat.user_pdf_index import UserPdfIndex

__all__ = [
    "ChatAbTestAssignment",
    "ChatAbuseFlag",
    "ChatAddonPurchase",
    "ChatConversation",
    "ChatDailyMetrics",
    "ChatFeatureFlag",
    "ChatMessage",
    "ChatQuotaUsage",
    "ChatSystemSetting",
    "ChatSystemSettingHistory",
    "KbDocument",
    "KbChunk",
    "RateLimitBucket",
    "SemanticCacheEntry",
    "UserPdfIndex",
    "UserPdfChunk",
]
