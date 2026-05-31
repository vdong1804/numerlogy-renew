"""Pydantic v2 schemas for authentication endpoints."""

from typing import Optional

from pydantic import BaseModel, EmailStr, field_validator


class RegisterIn(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    # Cloudflare Turnstile token — required in prod, optional in dev (secret empty)
    captcha_token: Optional[str] = None

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class TokenOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshIn(BaseModel):
    refresh_token: str


class UserOut(BaseModel):
    id: int
    email: str
    first_name: str
    last_name: str
    is_superuser: bool

    model_config = {"from_attributes": True}


class ForgotPasswordIn(BaseModel):
    email: EmailStr
    # Cloudflare Turnstile token — required in prod, optional in dev (secret empty)
    captcha_token: Optional[str] = None


class ResetPasswordIn(BaseModel):
    token: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v
