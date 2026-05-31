# ruff: noqa: UP017, I001
"""Tests for PackageOut coercion and PackageCreate/PackageUpdate validators (H5 + C3)."""

from __future__ import annotations

import pytest

from app.schemas.package import PackageCreate, PackageOut, PackageUpdate


# ---------------------------------------------------------------------------
# H5 — PackageOut coerces NULL package_kind to default
# ---------------------------------------------------------------------------


def test_package_out_coerces_null_package_kind_to_pdf_download():
    """NULL package_kind (raw insert / downgrade script) → coerced to 'pdf_download'."""
    data = {
        "id": 1,
        "name": "Legacy Pack",
        "price": 99000.0,
        "price_sale": 99000.0,
        "number_download": 5,
        "package_kind": None,  # simulates DB row with NULL
    }
    out = PackageOut.model_validate(data)
    assert out.package_kind == "pdf_download"


def test_package_out_preserves_explicit_chat_addon_kind():
    """Explicit 'chat_addon' is not coerced away."""
    data = {
        "id": 2,
        "name": "Addon Pack",
        "price": 49000.0,
        "price_sale": 49000.0,
        "number_download": 0,
        "package_kind": "chat_addon",
        "message_count": 50,
        "tier": "pro",
        "validity_days": 30,
    }
    out = PackageOut.model_validate(data)
    assert out.package_kind == "chat_addon"


def test_package_out_preserves_explicit_pdf_download_kind():
    """Explicit 'pdf_download' passes through unchanged."""
    data = {
        "id": 3,
        "name": "PDF Pack",
        "price": 99000.0,
        "price_sale": 99000.0,
        "number_download": 3,
        "package_kind": "pdf_download",
    }
    out = PackageOut.model_validate(data)
    assert out.package_kind == "pdf_download"


def test_package_out_empty_string_package_kind_coerced_to_pdf_download():
    """Empty string (not just None) should also fall back to default."""
    data = {
        "id": 4,
        "name": "Empty Kind Pack",
        "price": 0.0,
        "price_sale": 0.0,
        "number_download": 0,
        "package_kind": "",
    }
    out = PackageOut.model_validate(data)
    assert out.package_kind == "pdf_download"


# ---------------------------------------------------------------------------
# C3 — PackageCreate rejects invalid chat_addon combinations
# ---------------------------------------------------------------------------


def test_package_create_chat_addon_requires_message_count():
    with pytest.raises(ValueError, match="message_count"):
        PackageCreate(
            name="Bad",
            package_kind="chat_addon",
            message_count=None,
            tier="pro",
            validity_days=30,
        )


def test_package_create_chat_addon_requires_message_count_ge_1():
    with pytest.raises(ValueError, match="message_count"):
        PackageCreate(
            name="Bad",
            package_kind="chat_addon",
            message_count=0,
            tier="flash",
            validity_days=7,
        )


def test_package_create_chat_addon_requires_tier():
    with pytest.raises(ValueError, match="tier"):
        PackageCreate(
            name="Bad",
            package_kind="chat_addon",
            message_count=10,
            tier=None,
            validity_days=30,
        )


def test_package_create_chat_addon_requires_validity_days():
    with pytest.raises(ValueError, match="validity_days"):
        PackageCreate(
            name="Bad",
            package_kind="chat_addon",
            message_count=10,
            tier="pro",
            validity_days=None,
        )


def test_package_create_chat_addon_valid():
    pkg = PackageCreate(
        name="Good",
        package_kind="chat_addon",
        message_count=50,
        tier="pro",
        validity_days=30,
    )
    assert pkg.message_count == 50
    assert pkg.tier == "pro"
    assert pkg.validity_days == 30


def test_package_create_pdf_download_does_not_require_addon_fields():
    """pdf_download with no addon fields is valid."""
    pkg = PackageCreate(name="PDF", package_kind="pdf_download", number_download=5)
    assert pkg.package_kind == "pdf_download"
    assert pkg.message_count is None


# ---------------------------------------------------------------------------
# C3 — PackageUpdate: only validates when package_kind explicitly set
# ---------------------------------------------------------------------------


def test_package_update_chat_addon_validates_required_fields():
    with pytest.raises(ValueError, match="message_count"):
        PackageUpdate(package_kind="chat_addon", tier="pro", validity_days=30)


def test_package_update_no_kind_change_skips_validation():
    """package_kind=None means partial update — addon field check must NOT run."""
    upd = PackageUpdate(name="Rename only", package_kind=None)
    assert upd.name == "Rename only"
    assert upd.package_kind is None
