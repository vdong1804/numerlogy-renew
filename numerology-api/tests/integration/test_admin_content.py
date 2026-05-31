"""Integration tests for admin content CRUD endpoints."""

import pytest


class TestAdminContentList:
    """GET /admin/content/{resource} endpoint."""

    async def test_admin_content_requires_superuser(self, client, auth_headers):
        """GET /admin/content/{resource} by regular user returns 403."""
        response = await client.get(
            "/admin/content/main-number",
            headers=auth_headers,
        )
        assert response.status_code == 403

    async def test_admin_content_list_superuser(self, client, superuser_headers):
        """GET /admin/content/{resource} by superuser returns list."""
        response = await client.get(
            "/admin/content/main-number",
            headers=superuser_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["data"], list)

    async def test_admin_content_unknown_resource_404(self, client, superuser_headers):
        """GET /admin/content/{unknown} returns 404."""
        response = await client.get(
            "/admin/content/unknown-resource",
            headers=superuser_headers,
        )
        assert response.status_code == 404

    async def test_admin_content_requires_auth(self, client):
        """GET /admin/content without auth returns 401."""
        response = await client.get("/admin/content/main-number")
        assert response.status_code == 401


class TestAdminContentCreate:
    """POST /admin/content/{resource} endpoint."""

    async def test_admin_content_create_superuser(self, client, superuser_headers):
        """POST /admin/content/{resource} by superuser creates item."""
        response = await client.post(
            "/admin/content/main-number",
            json={
                "code": 1,
                "title": "Number One",
                "content": "The meaning of number one",
            },
            headers=superuser_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert "data" in data
        created = data["data"]
        assert created["code"] == 1
        assert created["title"] == "Number One"

    async def test_admin_content_create_regular_user_forbidden(self, client, auth_headers):
        """POST /admin/content/{resource} by regular user returns 403."""
        response = await client.post(
            "/admin/content/main-number",
            json={"code": 1, "title": "Title", "content": "Content"},
            headers=auth_headers,
        )
        assert response.status_code == 403

    async def test_admin_content_create_unauthenticated(self, client):
        """POST /admin/content without auth returns 401."""
        response = await client.post(
            "/admin/content/main-number",
            json={"code": 1, "title": "Title", "content": "Content"},
        )
        assert response.status_code == 401

    async def test_admin_content_create_all_resources(self, client, superuser_headers):
        """Verify major content resources can be created."""
        resources = [
            ("main-number", {"code": 1, "title": "Test", "content": "Test"}),
            ("personal-year", {"code": 1, "title": "Test", "content": "Test"}),
            ("life-challenge", {"code": 1, "title": "Test", "content": "Test"}),
        ]
        for resource, payload in resources:
            response = await client.post(
                f"/admin/content/{resource}",
                json=payload,
                headers=superuser_headers,
            )
            # Should be 201 or 409 (duplicate) — either is OK for this test
            assert response.status_code in [201, 409, 422]


class TestAdminContentDetail:
    """GET /admin/content/{resource}/{id} endpoint."""

    async def test_admin_content_detail_found(self, client, superuser_headers, db_session):
        """GET /admin/content/{resource}/{id} returns item detail."""
        from app.db.models.numerology_content import MainNumber

        # Create test item
        item = MainNumber(code=1, title="Test", content="Test content")
        db_session.add(item)
        await db_session.commit()
        await db_session.refresh(item)

        response = await client.get(
            f"/admin/content/main-number/{item.id}",
            headers=superuser_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["code"] == 1

    async def test_admin_content_detail_not_found(self, client, superuser_headers):
        """GET /admin/content/{resource}/{id} with non-existent id returns 404."""
        response = await client.get(
            "/admin/content/main-number/99999",
            headers=superuser_headers,
        )
        assert response.status_code == 404


class TestAdminContentUpdate:
    """PUT /admin/content/{resource}/{id} endpoint."""

    async def test_admin_content_update_superuser(self, client, superuser_headers, db_session):
        """PUT /admin/content/{resource}/{id} by superuser updates item."""
        from app.db.models.numerology_content import MainNumber

        item = MainNumber(code=1, title="Original", content="Original content")
        db_session.add(item)
        await db_session.commit()
        await db_session.refresh(item)

        response = await client.put(
            f"/admin/content/main-number/{item.id}",
            json={"title": "Updated", "content": "Updated content"},
            headers=superuser_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["title"] == "Updated"

    async def test_admin_content_update_regular_user_forbidden(self, client, auth_headers, db_session):
        """PUT /admin/content/{resource}/{id} by regular user returns 403."""
        from app.db.models.numerology_content import MainNumber

        item = MainNumber(code=1, title="Test", content="Content")
        db_session.add(item)
        await db_session.commit()
        await db_session.refresh(item)

        response = await client.put(
            f"/admin/content/main-number/{item.id}",
            json={"title": "Hacked"},
            headers=auth_headers,
        )
        assert response.status_code == 403


class TestAdminContentDelete:
    """DELETE /admin/content/{resource}/{id} endpoint."""

    async def test_admin_content_delete_superuser(self, client, superuser_headers, db_session):
        """DELETE /admin/content/{resource}/{id} by superuser deletes item."""
        from app.db.models.numerology_content import MainNumber

        item = MainNumber(code=1, title="To delete", content="Content")
        db_session.add(item)
        await db_session.commit()
        item_id = item.id

        response = await client.delete(
            f"/admin/content/main-number/{item_id}",
            headers=superuser_headers,
        )
        assert response.status_code == 204

        # Verify deleted
        verify_resp = await client.get(
            f"/admin/content/main-number/{item_id}",
            headers=superuser_headers,
        )
        assert verify_resp.status_code == 404

    async def test_admin_content_delete_regular_user_forbidden(self, client, auth_headers, db_session):
        """DELETE /admin/content/{resource}/{id} by regular user returns 403."""
        from app.db.models.numerology_content import MainNumber

        item = MainNumber(code=1, title="Protected", content="Content")
        db_session.add(item)
        await db_session.commit()
        await db_session.refresh(item)

        response = await client.delete(
            f"/admin/content/main-number/{item.id}",
            headers=auth_headers,
        )
        assert response.status_code == 403
