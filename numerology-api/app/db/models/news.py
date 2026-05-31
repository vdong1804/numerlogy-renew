"""SQLAlchemy 2.0 model for news articles."""

from typing import Optional

from sqlalchemy import BigInteger, SmallInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.mixins import TimestampMixin


class News(TimestampMixin, Base):
    __tablename__ = "news"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    short_content: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    # 1=general (default), extensible for future categories
    category: Mapped[int] = mapped_column(SmallInteger, default=1, nullable=False)
    image: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)


__all__ = ["News"]
