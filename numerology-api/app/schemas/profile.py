"""Pydantic schemas for user profile endpoints."""

from typing import Optional

from pydantic import BaseModel, ConfigDict, computed_field


class ProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    first_name: str
    last_name: str

    @computed_field
    @property
    def name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()

    # Nested profile fields — flattened via validator on router side
    birth_day: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    number_download: int = 0


class ProfileNestedOut(BaseModel):
    """Matches Django UserProfileSerializer nested in UserSerializer."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    birth_day: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    number_download: int = 0


class UserWithProfileOut(BaseModel):
    """Top-level shape matching Django UserSerializer: {id, email, profile}."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    profile: Optional[ProfileNestedOut] = None


class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    birth_day: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
