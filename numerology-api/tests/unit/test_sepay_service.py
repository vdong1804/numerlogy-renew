"""Unit tests for sepay_service helpers (parse / verify)."""

import pytest

from app.config import settings
from app.services.sepay_service import parse_ref_code, verify_apikey


@pytest.mark.parametrize(
    "text,expected",
    [
        ("Thanh toan don NSQ-A2K7XJ9R", "NSQ-A2K7XJ9R"),
        ("nsq-bmcdvwxz nay khong nen match vi viet thuong", "NSQ-BMCDVWXZ"),  # we upper() before regex
        ("Khong co ma trong noi dung nay", None),
        ("", None),
        ("Format sai NSQ-ABC (qua ngan)", None),
        ("Co loi sai NSQ-ABCDEFG1 chinh xac 8 ky tu", "NSQ-ABCDEFG1"),
        ("Mid-word match khongNSQ-23456789kfoo", None),  # word boundary should reject embedded
    ],
)
def test_parse_ref_code(text, expected):
    assert parse_ref_code(text) == expected


def test_verify_apikey_constant_time(monkeypatch):
    monkeypatch.setattr(settings, "sepay_api_key", "secret-key-123")
    assert verify_apikey("Apikey secret-key-123") is True
    assert verify_apikey("secret-key-123") is True  # bare token accepted
    assert verify_apikey("Apikey wrong") is False
    assert verify_apikey(None) is False
    assert verify_apikey("") is False


def test_verify_apikey_denied_when_unconfigured(monkeypatch):
    monkeypatch.setattr(settings, "sepay_api_key", "")
    assert verify_apikey("Apikey anything") is False
