"""Integration tests for profile and news endpoints."""

import pytest


class TestProfileGet:
    """GET /api/profile endpoint."""

    async def test_get_profile_auto_creates(self, client, user, auth_headers):
        """GET /api/profile auto-creates profile on first call."""
        response = await client.get("/api/profile", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        profile = data["data"]
        assert profile["id"] == user.id
        assert profile["email"] == user.email
        assert "profile" in profile

    async def test_get_profile_without_auth(self, client):
        """GET /api/profile without token returns 401."""
        response = await client.get("/api/profile")
        assert response.status_code == 401

    async def test_get_profile_existing(self, client, user_with_profile, auth_headers):
        """GET /api/profile returns existing profile."""
        response = await client.get("/api/profile", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        profile = data["data"]["profile"]
        assert profile["birth_day"] == user_with_profile.profile.birth_day


class TestProfileUpdate:
    """PUT /api/profile endpoint."""

    async def test_update_profile_happy_path(self, client, user_with_profile, auth_headers):
        """PUT /api/profile updates profile fields."""
        response = await client.put(
            "/api/profile",
            json={
                "name": "Updated Name",
                "phone": "0987654321",
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        profile = data["data"]["profile"]
        assert profile["name"] == "Updated Name"
        assert profile["phone"] == "0987654321"

    async def test_update_profile_partial(self, client, user_with_profile, auth_headers):
        """PUT /api/profile with partial update."""
        original_birth_day = user_with_profile.profile.birth_day
        response = await client.put(
            "/api/profile",
            json={"name": "New Name"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        profile = response.json()["data"]["profile"]
        assert profile["name"] == "New Name"
        assert profile["birth_day"] == original_birth_day

    async def test_update_profile_without_auth(self, client):
        """PUT /api/profile without token returns 401."""
        response = await client.put(
            "/api/profile",
            json={"name": "Test"},
        )
        assert response.status_code == 401

    async def test_update_profile_creates_if_missing(self, client, user, auth_headers):
        """PUT /api/profile creates profile if it doesn't exist."""
        response = await client.put(
            "/api/profile",
            json={
                "name": "Created Name",
                "birth_day": "01011990",
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        profile = response.json()["data"]["profile"]
        assert profile["name"] == "Created Name"


class TestNewsTop:
    """GET /api/news-top endpoint."""

    async def test_news_top_empty(self, client, db_session):
        """GET /api/news-top with no data returns empty list."""
        response = await client.get("/api/news-top")
        assert response.status_code == 200
        data = response.json()
        assert data["data"] == []

    async def test_news_top_with_data(self, client, db_session):
        """GET /api/news-top returns top 10 category=1 news."""
        from app.db.models.news import News

        # Create test news
        for i in range(15):
            news = News(
                title=f"News {i}",
                content=f"Content {i}",
                category=1 if i < 10 else 2,  # First 10 are category 1
            )
            db_session.add(news)
        await db_session.commit()

        response = await client.get("/api/news-top")
        assert response.status_code == 200
        data = response.json()
        # Should have up to 10 category=1 items
        assert len(data["data"]) <= 10


class TestNewsList:
    """GET /api/news endpoint (paginated)."""

    async def test_news_list_empty(self, client):
        """GET /api/news with no data returns empty paginated response."""
        response = await client.get("/api/news")
        assert response.status_code == 200
        data = response.json()
        assert data["data"] == []
        assert "total" in data
        assert "limit" in data
        assert "offset" in data

    async def test_news_list_pagination(self, client, db_session):
        """GET /api/news with pagination params."""
        from app.db.models.news import News

        # Create 25 news items
        for i in range(25):
            news = News(title=f"News {i}", content=f"Content {i}", category=1)
            db_session.add(news)
        await db_session.commit()

        # Get first page
        response = await client.get("/api/news?limit=10&offset=0")
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 10
        assert data["total"] == 25


class TestNewsDetail:
    """GET /api/news/{id} endpoint."""

    async def test_news_detail_found(self, client, db_session):
        """GET /api/news/{id} returns news detail."""
        from app.db.models.news import News

        news = News(title="Test News", content="Test content", category=1)
        db_session.add(news)
        await db_session.commit()
        await db_session.refresh(news)

        response = await client.get(f"/api/news/{news.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["title"] == "Test News"

    async def test_news_detail_not_found(self, client):
        """GET /api/news/{id} with non-existent id returns 404."""
        response = await client.get("/api/news/99999")
        assert response.status_code == 404


class TestNewsCreate:
    """POST /api/news endpoint (superuser only)."""

    async def test_news_create_superuser(self, client, superuser_headers, db_session):
        """POST /api/news by superuser creates news."""
        response = await client.post(
            "/api/news",
            json={
                "title": "New News",
                "content": "New content",
                "category": 1,
            },
            headers=superuser_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["data"]["title"] == "New News"

    async def test_news_create_regular_user_forbidden(self, client, auth_headers):
        """POST /api/news by regular user returns 403."""
        response = await client.post(
            "/api/news",
            json={
                "title": "Unauthorized News",
                "content": "Content",
                "category": 1,
            },
            headers=auth_headers,
        )
        assert response.status_code == 403

    async def test_news_create_unauthenticated(self, client):
        """POST /api/news without token returns 401."""
        response = await client.post(
            "/api/news",
            json={
                "title": "News",
                "content": "Content",
                "category": 1,
            },
        )
        assert response.status_code == 401


class TestNewsUpdate:
    """PUT /api/news/{id} endpoint (superuser only)."""

    async def test_news_update_superuser(self, client, superuser_headers, db_session):
        """PUT /api/news/{id} by superuser updates news."""
        from app.db.models.news import News

        news = News(title="Original", content="Original content", category=1)
        db_session.add(news)
        await db_session.commit()
        await db_session.refresh(news)

        response = await client.put(
            f"/api/news/{news.id}",
            json={"title": "Updated", "content": "Updated content"},
            headers=superuser_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["title"] == "Updated"

    async def test_news_update_regular_user_forbidden(self, client, auth_headers, db_session):
        """PUT /api/news/{id} by regular user returns 403."""
        from app.db.models.news import News

        news = News(title="Test", content="Content", category=1)
        db_session.add(news)
        await db_session.commit()
        await db_session.refresh(news)

        response = await client.put(
            f"/api/news/{news.id}",
            json={"title": "Hacked"},
            headers=auth_headers,
        )
        assert response.status_code == 403


class TestNewsDelete:
    """DELETE /api/news/{id} endpoint (superuser only)."""

    async def test_news_delete_superuser(self, client, superuser_headers, db_session):
        """DELETE /api/news/{id} by superuser deletes news."""
        from app.db.models.news import News

        news = News(title="To delete", content="Content", category=1)
        db_session.add(news)
        await db_session.commit()
        news_id = news.id

        response = await client.delete(
            f"/api/news/{news_id}",
            headers=superuser_headers,
        )
        assert response.status_code == 204

        # Verify deleted
        verify_resp = await client.get(f"/api/news/{news_id}")
        assert verify_resp.status_code == 404

    async def test_news_delete_regular_user_forbidden(self, client, auth_headers, db_session):
        """DELETE /api/news/{id} by regular user returns 403."""
        from app.db.models.news import News

        news = News(title="Protected", content="Content", category=1)
        db_session.add(news)
        await db_session.commit()
        await db_session.refresh(news)

        response = await client.delete(
            f"/api/news/{news.id}",
            headers=auth_headers,
        )
        assert response.status_code == 403
