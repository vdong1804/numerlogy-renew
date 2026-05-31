"""Unit tests for order_service.create_order and helpers."""

import pytest
from fastapi import HTTPException
from sqlalchemy import select

from app.db.models.product import Product
from app.schemas.order import OrderCreateRequest, OrderItemInput
from app.services.order_service import create_order


async def _add_product(db, **overrides) -> Product:
    p = Product(
        sku=overrides.pop("sku", "test-pkg"),
        type=overrides.pop("type", "package"),
        name=overrides.pop("name", "Test Package"),
        slug=overrides.pop("slug", "test-package"),
        price=overrides.pop("price", 99000),
        is_active=overrides.pop("is_active", True),
        **overrides,
    )
    db.add(p)
    await db.flush()
    await db.refresh(p)
    return p


async def test_create_order_computes_total_server_side(db_session, user):
    p1 = await _add_product(db_session, sku="p1", slug="p1", price=50000)
    p2 = await _add_product(db_session, sku="p2", slug="p2", price=120000)

    body = OrderCreateRequest(
        items=[OrderItemInput(product_id=p1.id, qty=2), OrderItemInput(product_id=p2.id, qty=1)]
    )
    order = await create_order(db_session, user.id, body)

    assert order.user_id == user.id
    assert order.total_amount == 50000 * 2 + 120000
    assert order.ref_code.startswith("NSQ-")
    assert len(order.items) == 2
    assert order.status == "pending"


async def test_create_order_rejects_missing_product(db_session, user):
    body = OrderCreateRequest(items=[OrderItemInput(product_id=999999, qty=1)])
    with pytest.raises(HTTPException) as exc:
        await create_order(db_session, user.id, body)
    assert exc.value.status_code == 400


async def test_create_order_rejects_inactive_product(db_session, user):
    p = await _add_product(db_session, sku="inactive", slug="inactive", is_active=False)
    body = OrderCreateRequest(items=[OrderItemInput(product_id=p.id, qty=1)])
    with pytest.raises(HTTPException):
        await create_order(db_session, user.id, body)
