"""Tests for report_entitlement_service: tier resolution + identity matching."""

from datetime import datetime, timedelta, timezone

import pytest

from app.db.models.order import Order, OrderItem
from app.db.models.package import Package, UserPackage
from app.db.models.product import Product
from app.db.models.user import UserProfile
from app.db.models.user_report import UserReport
from app.services.report_entitlement_service import (
    ALL_SECTIONS,
    FREE_SECTIONS,
    find_order_report_download_id,
    normalize_name,
    resolve_entitlement,
)

_NAME = "Nguyễn Văn A"
_BIRTH = "15101990"


async def _make_paid_order(
    db_session, user, *, name=_NAME, birth_day=_BIRTH, product_type="report"
) -> Order:
    product = Product(
        sku=f"sku-{product_type}", type=product_type, name="Báo cáo",
        slug=f"slug-{product_type}", price=100000,
    )
    db_session.add(product)
    await db_session.flush()

    order = Order(
        user_id=user.id,
        ref_code=f"REF{product_type[:3].upper()}1",
        total_amount=100000,
        currency="VND",
        status="paid",
        payment_method="sepay",
        expires_at=datetime.now(timezone.utc) + timedelta(days=1),
        paid_at=datetime.now(timezone.utc),
        meta={"name": name, "birth_day": birth_day, "phone": "0900000000"},
    )
    order.items.append(
        OrderItem(product_id=product.id, qty=1, unit_price=100000, snapshot_name="Báo cáo")
    )
    db_session.add(order)
    await db_session.flush()
    return order


async def _grant_package(db_session, user, *, is_used=True, expires_at=None) -> UserPackage:
    pkg = Package(name="Premium", price=99000, price_sale=99000, number_download=14)
    db_session.add(pkg)
    await db_session.flush()
    up = UserPackage(
        user_id=user.id, package_id=pkg.id, is_used=is_used, expires_at=expires_at
    )
    db_session.add(up)
    await db_session.flush()
    return up


class TestNormalize:
    def test_accent_and_case_folding(self):
        assert normalize_name(" Nguyễn  Văn  A ") == "nguyen van a"

    def test_d_stroke(self):
        assert normalize_name("Đỗ Đình") == "do dinh"


class TestResolveEntitlement:
    async def test_anonymous_is_free(self, db_session):
        tier, unlocked, oid, _ = await resolve_entitlement(db_session, None, _NAME, _BIRTH)
        assert tier == "free"
        assert unlocked == FREE_SECTIONS
        assert oid is None

    async def test_paid_order_matching_identity_unlocks_all(self, db_session, user):
        order = await _make_paid_order(db_session, user)
        tier, unlocked, oid, _ = await resolve_entitlement(db_session, user, _NAME, _BIRTH)
        assert tier == "paid"
        assert unlocked == ALL_SECTIONS
        assert oid == order.id

    async def test_identity_match_is_accent_insensitive(self, db_session, user):
        await _make_paid_order(db_session, user, name="nguyen van a")
        # Viewer typed the accented form; order stored unaccented → still matches.
        tier, _, _, _ = await resolve_entitlement(db_session, user, "Nguyễn Văn A", _BIRTH)
        assert tier == "paid"

    async def test_mismatched_identity_stays_free(self, db_session, user):
        await _make_paid_order(db_session, user, name="Someone Else")
        tier, unlocked, oid, _ = await resolve_entitlement(db_session, user, _NAME, _BIRTH)
        assert tier == "free"
        assert oid is None

    async def test_pending_order_does_not_unlock(self, db_session, user):
        order = await _make_paid_order(db_session, user)
        order.status = "pending"
        await db_session.flush()
        tier, _, _, _ = await resolve_entitlement(db_session, user, _NAME, _BIRTH)
        assert tier == "free"

    async def test_package_only_order_does_not_unlock_summary(self, db_session, user):
        # Pure package (not report/combo) → no summary unlock in v1.
        await _make_paid_order(db_session, user, product_type="package")
        tier, _, _, _ = await resolve_entitlement(db_session, user, _NAME, _BIRTH)
        assert tier == "free"

    async def test_combo_order_unlocks(self, db_session, user):
        await _make_paid_order(db_session, user, product_type="combo")
        tier, unlocked, _, _ = await resolve_entitlement(db_session, user, _NAME, _BIRTH)
        assert tier == "paid"
        assert unlocked == ALL_SECTIONS

    async def test_active_package_unlocks_any_lookup(self, db_session, user):
        # Premium subscriber — unlocks even a name they never purchased a report for.
        await _grant_package(db_session, user)
        tier, unlocked, oid, src = await resolve_entitlement(
            db_session, user, "Totally Different Name", "01011980"
        )
        assert tier == "paid"
        assert unlocked == ALL_SECTIONS
        assert oid is None
        assert src == "quota"

    async def test_active_package_with_future_expiry_unlocks(self, db_session, user):
        await _grant_package(
            db_session, user, expires_at=datetime.now(timezone.utc) + timedelta(days=30)
        )
        tier, _, _, src = await resolve_entitlement(db_session, user, _NAME, _BIRTH)
        assert tier == "paid"
        assert src == "quota"

    async def test_expired_package_does_not_unlock(self, db_session, user):
        await _grant_package(
            db_session, user, expires_at=datetime.now(timezone.utc) - timedelta(days=1)
        )
        tier, _, _, src = await resolve_entitlement(db_session, user, _NAME, _BIRTH)
        assert tier == "free"
        assert src == "free"

    async def test_unused_package_does_not_unlock(self, db_session, user):
        await _grant_package(db_session, user, is_used=False)
        tier, _, _, _ = await resolve_entitlement(db_session, user, _NAME, _BIRTH)
        assert tier == "free"

    async def test_remaining_download_quota_unlocks(self, db_session, user):
        # Premium signalled only by leftover download quota (legacy/edge data).
        db_session.add(
            UserProfile(user_id=user.id, name="x", birth_day="01011990", number_download=14)
        )
        await db_session.flush()
        tier, _, _, src = await resolve_entitlement(db_session, user, _NAME, _BIRTH)
        assert tier == "paid"
        assert src == "quota"


class TestFindOrderReportDownloadId:
    async def test_none_when_no_report(self, db_session, user):
        order = await _make_paid_order(db_session, user)
        assert await find_order_report_download_id(db_session, order.id) is None

    async def test_returns_latest_non_refunded(self, db_session, user):
        order = await _make_paid_order(db_session, user)
        product_id = order.items[0].product_id
        db_session.add(
            UserReport(
                user_id=user.id, order_id=order.id, product_id=product_id,
                pdf_path="reports/202606/a.pdf", input_payload={},
            )
        )
        await db_session.flush()
        rid = await find_order_report_download_id(db_session, order.id)
        assert rid is not None

    async def test_skips_refunded(self, db_session, user):
        order = await _make_paid_order(db_session, user)
        product_id = order.items[0].product_id
        db_session.add(
            UserReport(
                user_id=user.id, order_id=order.id, product_id=product_id,
                pdf_path="REFUNDED/reports/202606/a.pdf", input_payload={},
            )
        )
        await db_session.flush()
        assert await find_order_report_download_id(db_session, order.id) is None
