"""Integration: GET /api/numerology-report entitlement wiring (free vs paid)."""

from datetime import datetime, timedelta, timezone

import pytest

from app.db.models.order import Order, OrderItem
from app.db.models.product import Product

_URL = "/api/numerology-report"
_NAME = "Nguyễn Văn A"
_BIRTH = "15101990"
_PARAMS = {"full_name": _NAME, "birth_day": _BIRTH, "phone": "0900000000"}


async def _seed_paid_report_order(db_session, user):
    product = Product(sku="rep-1", type="report", name="Báo cáo", slug="rep-1", price=100000)
    db_session.add(product)
    await db_session.flush()
    order = Order(
        user_id=user.id, ref_code="REFINT1", total_amount=100000, currency="VND",
        status="paid", payment_method="sepay",
        expires_at=datetime.now(timezone.utc) + timedelta(days=1),
        paid_at=datetime.now(timezone.utc),
        meta={"name": _NAME, "birth_day": _BIRTH},
    )
    order.items.append(
        OrderItem(product_id=product.id, qty=1, unit_price=100000, snapshot_name="Báo cáo")
    )
    db_session.add(order)
    await db_session.commit()


class TestReportEntitlementEndpoint:
    async def test_anonymous_free_tier_locks_core(self, client):
        res = await client.get(_URL, params=_PARAMS)
        assert res.status_code == 200
        body = res.json()
        assert body["tier"] == "free"
        # Core numbers locked + content stripped for anonymous viewers.
        su_menh = body["data"]["core_numbers"]["su_menh"]
        assert su_menh["locked"] is True
        assert su_menh["content"] is None

    async def test_invalid_token_treated_as_free(self, client):
        res = await client.get(
            _URL, params=_PARAMS, headers={"Authorization": "Bearer not-a-real-token"}
        )
        assert res.status_code == 200
        assert res.json()["tier"] == "free"

    async def test_paid_user_unlocks_full_report(self, client, db_session, user, auth_headers):
        await _seed_paid_report_order(db_session, user)
        res = await client.get(_URL, params=_PARAMS, headers=auth_headers)
        assert res.status_code == 200
        body = res.json()
        assert body["tier"] == "paid"
        assert body["matched_order_id"] is not None
        assert "locked" not in body["data"]["core_numbers"]["su_menh"]
