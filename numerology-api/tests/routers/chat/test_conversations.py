"""Integration tests for /api/chat/conversations CRUD."""

import pytest


class TestCreateConversation:
    async def test_create_returns_201(self, client, auth_headers):
        resp = await client.post(
            "/api/chat/conversations",
            json={"title": "Numerology Q&A"},
            headers=auth_headers,
        )
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["title"] == "Numerology Q&A"
        assert data["id"] > 0

    async def test_create_unauthenticated_401(self, client):
        resp = await client.post("/api/chat/conversations", json={"title": "x"})
        assert resp.status_code == 401

    async def test_create_without_title_ok(self, client, auth_headers):
        resp = await client.post(
            "/api/chat/conversations", json={}, headers=auth_headers
        )
        assert resp.status_code == 201
        assert resp.json()["data"]["title"] is None


class TestListConversations:
    async def test_list_returns_only_own(self, client, auth_headers):
        # create two
        await client.post(
            "/api/chat/conversations", json={"title": "A"}, headers=auth_headers
        )
        await client.post(
            "/api/chat/conversations", json={"title": "B"}, headers=auth_headers
        )
        resp = await client.get("/api/chat/conversations", headers=auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 2
        assert {c["title"] for c in body["data"]} == {"A", "B"}


class TestGetConversation:
    async def test_get_own_returns_200(self, client, auth_headers):
        created = (
            await client.post(
                "/api/chat/conversations",
                json={"title": "Own"},
                headers=auth_headers,
            )
        ).json()["data"]
        resp = await client.get(
            f"/api/chat/conversations/{created['id']}", headers=auth_headers
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["id"] == created["id"]

    async def test_get_other_users_returns_404(self, client, auth_headers, superuser_headers):
        # create as superuser
        created = (
            await client.post(
                "/api/chat/conversations",
                json={"title": "Admins"},
                headers=superuser_headers,
            )
        ).json()["data"]
        # try to fetch as regular user
        resp = await client.get(
            f"/api/chat/conversations/{created['id']}", headers=auth_headers
        )
        assert resp.status_code == 404


class TestDeleteConversation:
    async def test_delete_own_returns_204(self, client, auth_headers):
        created = (
            await client.post(
                "/api/chat/conversations",
                json={"title": "Doomed"},
                headers=auth_headers,
            )
        ).json()["data"]
        resp = await client.delete(
            f"/api/chat/conversations/{created['id']}", headers=auth_headers
        )
        assert resp.status_code == 204

        # GET should now 404
        resp2 = await client.get(
            f"/api/chat/conversations/{created['id']}", headers=auth_headers
        )
        assert resp2.status_code == 404

    async def test_delete_other_users_returns_404(self, client, auth_headers, superuser_headers):
        created = (
            await client.post(
                "/api/chat/conversations",
                json={"title": "Mine"},
                headers=superuser_headers,
            )
        ).json()["data"]
        resp = await client.delete(
            f"/api/chat/conversations/{created['id']}", headers=auth_headers
        )
        assert resp.status_code == 404
