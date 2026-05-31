"""Pydantic v2 query-param schemas for numerology endpoints."""

import re
from typing import Optional

from pydantic import BaseModel, field_validator, model_validator


class SoHocQuery(BaseModel):
    """Paid numerology report — requires auth."""

    full_name: str
    birth_day: str
    phone: str
    sex: int = 1
    birth_time: Optional[str] = None
    job: Optional[str] = None

    # Extra params passed by frontend for paid PDF layout
    r: str = ''
    l: str = ''
    eq: str = ''
    iq: str = ''
    aq: str = ''
    cq: str = ''
    v: str = ''
    a: str = ''
    k: str = ''
    r1_1: str = ''
    r1_2: str = ''
    r2_1: str = ''
    r2_2: str = ''
    r3_1: str = ''
    r3_2: str = ''
    r4_1: str = ''
    r4_2: str = ''
    r5_1: str = ''
    r5_2: str = ''
    l1_1: str = ''
    l1_2: str = ''
    l2_1: str = ''
    l2_2: str = ''
    l3_1: str = ''
    l3_2: str = ''
    l4_1: str = ''
    l4_2: str = ''
    l5_1: str = ''
    l5_2: str = ''
    type_iq_1: str = ''
    type_iq_2: str = ''
    type_iq_3: str = ''
    type_iq_4: str = ''
    type_iq_5: str = ''
    type_iq_6: str = ''
    type_iq_7: str = ''
    type_iq_8: str = ''

    @field_validator('full_name')
    @classmethod
    def validate_full_name(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError('Vui lòng nhập họ tên')
        return stripped

    @field_validator('birth_day')
    @classmethod
    def validate_birth_day(cls, v: str) -> str:
        if not re.fullmatch(r'\d{8}', v):
            raise ValueError('Ngày sinh không hợp lệ (định dạng: ddmmyyyy)')
        return v

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v: str) -> str:
        return re.sub(r'\D', '', v)


class SoHocFreeQuery(BaseModel):
    """Free numerology report — public, phone required."""

    full_name: str
    birth_day: str
    phone: str

    @field_validator('full_name')
    @classmethod
    def validate_full_name(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError('Vui lòng nhập họ tên')
        return stripped

    @field_validator('birth_day')
    @classmethod
    def validate_birth_day(cls, v: str) -> str:
        if not re.fullmatch(r'\d{8}', v):
            raise ValueError('Ngày sinh không hợp lệ (định dạng: ddmmyyyy)')
        return v

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v: str) -> str:
        digits = re.sub(r'\D', '', v)
        if len(digits) < 3:
            raise ValueError('Số điện thoại không hợp lệ')
        return digits


class LasoQuery(BaseModel):
    """Astrology chart — calls vietheart.net horoscope API."""

    full_name: str
    birth_day: str
    birth_time: str
    sex: int = 1

    @field_validator('full_name')
    @classmethod
    def validate_full_name(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError('Vui lòng nhập họ tên')
        return stripped

    @field_validator('birth_day')
    @classmethod
    def validate_birth_day(cls, v: str) -> str:
        if not re.fullmatch(r'\d{8}', v):
            raise ValueError('Ngày sinh không hợp lệ (định dạng: ddmmyyyy)')
        return v
