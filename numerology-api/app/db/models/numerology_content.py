"""SQLAlchemy 2.0 models for all numerology content tables.

22 models sharing NumerologyContentMixin (DRY).
Each model ≤8 lines — only extras beyond mixin declared here.
"""

from typing import Optional

from sqlalchemy import BigInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.mixins import NumerologyContentMixin

# ---------------------------------------------------------------------------
# Standard content tables — mixin provides all columns
# ---------------------------------------------------------------------------


class MissionNumber(NumerologyContentMixin, Base):
    __tablename__ = "mission_number"


class SoulsNumber(NumerologyContentMixin, Base):
    __tablename__ = "souls_number"


class DevelopmentNumber(NumerologyContentMixin, Base):
    __tablename__ = "development_number"


class LifePeak(NumerologyContentMixin, Base):
    __tablename__ = "peak_life"


class ChallengeLife(NumerologyContentMixin, Base):
    __tablename__ = "challenge_life"


class BirthdayChart(NumerologyContentMixin, Base):
    __tablename__ = "birthday_chart"


class NameChart(NumerologyContentMixin, Base):
    __tablename__ = "name_chart"


class StagesOfLife(NumerologyContentMixin, Base):
    __tablename__ = "stages_of_life"


class AttitudeNumber(NumerologyContentMixin, Base):
    __tablename__ = "attitude_number"


class BirthdayNumber(NumerologyContentMixin, Base):
    __tablename__ = "birthday_number"


class MatureNumber(NumerologyContentMixin, Base):
    __tablename__ = "mature_number"


class IntrospectiveNumber(NumerologyContentMixin, Base):
    __tablename__ = "introspective_number"


class KarmicNumber(NumerologyContentMixin, Base):
    __tablename__ = "karmic_number"


class DeficitNumber(NumerologyContentMixin, Base):
    __tablename__ = "deficit_number"


class PhoneNumber(NumerologyContentMixin, Base):
    __tablename__ = "phone_number"


class PersonalMonthNumber(NumerologyContentMixin, Base):
    # Bug fix: Django had "personal month_number" (space in name) — corrected here
    __tablename__ = "personal_month_number"


class Identifiable(NumerologyContentMixin, Base):
    __tablename__ = "identifiable"


class MissNumber(NumerologyContentMixin, Base):
    __tablename__ = "miss_number"


class PersonalYearNumber(NumerologyContentMixin, Base):
    __tablename__ = "personal_year_number"


class KarmicDebtNumber(NumerologyContentMixin, Base):
    # Số Nợ Nghiệp — codes 13/14/16/19 (Karmic Debt)
    __tablename__ = "karmic_debt_number"


class GrowthNumber(NumerologyContentMixin, Base):
    # Số Phát Triển (Năng Lực Tiếp Cận) — maps to so_phat_trien
    __tablename__ = "growth_number"


# ---------------------------------------------------------------------------
# MainNumber — extends mixin with content_2..5 extra columns
# ---------------------------------------------------------------------------


class MainNumber(NumerologyContentMixin, Base):
    __tablename__ = "main_number"

    content_2: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    content_3: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    content_4: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    content_5: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


# ---------------------------------------------------------------------------
# PhoneMasterDataModel — only code + bow (no full content cols)
# Does NOT use NumerologyContentMixin — different schema shape.
# ---------------------------------------------------------------------------


class PhoneMasterDataModel(Base):
    __tablename__ = "phone_master_data"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(255), index=True, unique=True, nullable=False)
    bow: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)


__all__ = [
    "MainNumber",
    "MissionNumber",
    "SoulsNumber",
    "DevelopmentNumber",
    "LifePeak",
    "ChallengeLife",
    "BirthdayChart",
    "NameChart",
    "StagesOfLife",
    "AttitudeNumber",
    "BirthdayNumber",
    "MatureNumber",
    "IntrospectiveNumber",
    "KarmicNumber",
    "DeficitNumber",
    "PhoneNumber",
    "PersonalMonthNumber",
    "Identifiable",
    "MissNumber",
    "PersonalYearNumber",
    "KarmicDebtNumber",
    "GrowthNumber",
    "PhoneMasterDataModel",
]
