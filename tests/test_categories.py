"""Kategoriyalar CRUD."""
from tests.conftest import register, auth


class TestCategoryList:
    def test_list_empty(self, client):
        r = client.get("/api/v1/categories/")
        assert r.status_code == 200
        assert r.json() == []

    def test_list_with_data(self, client, category):
        r = client.get("/api/v1/categories/")
        assert len(r.json()) == 1
        assert r.json()[0]["slug"] == "games"


class TestCategoryGet:
    def test_get_by_slug(self, client, category):
        r = client.get(f"/api/v1/categories/{category['slug']}")
        assert r.status_code == 200
        assert r.json()["name"] == "Games"

    def test_get_nonexistent(self, client):
        r = client.get("/api/v1/categories/no-such-slug")
        assert r.status_code == 404

    def test_get_category_games(self, client, category, game):
        r = client.get(f"/api/v1/categories/{category['slug']}/games")
        assert r.status_code == 200
        assert len(r.json()) == 1


class TestCategoryCreate:
    def test_create_by_admin(self, client, admin_token):
        r = client.post("/api/v1/categories/",
                        json={"name": "Mobile", "slug": "mobile"},
                        headers=auth(admin_token))
        assert r.status_code == 201
        assert r.json()["slug"] == "mobile"

    def test_create_by_non_admin(self, client, user_token):
        r = client.post("/api/v1/categories/",
                        json={"name": "Test", "slug": "test"},
                        headers=auth(user_token))
        assert r.status_code == 403

    def test_duplicate_slug(self, client, admin_token, category):
        r = client.post("/api/v1/categories/",
                        json={"name": "Dup", "slug": "games"},
                        headers=auth(admin_token))
        assert r.status_code == 409


class TestCategoryDelete:
    def test_delete_by_admin(self, client, admin_token, category):
        r = client.delete(f"/api/v1/categories/{category['slug']}", headers=auth(admin_token))
        assert r.status_code == 204
        assert client.get(f"/api/v1/categories/{category['slug']}").status_code == 404

    def test_delete_by_non_admin(self, client, user_token, category):
        r = client.delete(f"/api/v1/categories/{category['slug']}", headers=auth(user_token))
        assert r.status_code == 403
