"""Sevimlilар."""
import uuid
from tests.conftest import register, auth


class TestFavorites:
    def test_add_favorite(self, client, user_token, product):
        r = client.post(f"/api/v1/favorites/{product['id']}", headers=auth(user_token))
        assert r.status_code == 201

    def test_add_duplicate_fails(self, client, user_token, product):
        client.post(f"/api/v1/favorites/{product['id']}", headers=auth(user_token))
        r = client.post(f"/api/v1/favorites/{product['id']}", headers=auth(user_token))
        assert r.status_code == 409

    def test_add_nonexistent_product(self, client, user_token):
        r = client.post(f"/api/v1/favorites/{uuid.uuid4()}", headers=auth(user_token))
        assert r.status_code == 404

    def test_list_favorites(self, client, user_token, product):
        client.post(f"/api/v1/favorites/{product['id']}", headers=auth(user_token))
        r = client.get("/api/v1/favorites/", headers=auth(user_token))
        assert r.status_code == 200
        assert r.json()["total"] == 1

    def test_list_empty(self, client, user_token):
        r = client.get("/api/v1/favorites/", headers=auth(user_token))
        assert r.json()["total"] == 0

    def test_remove_favorite(self, client, user_token, product):
        client.post(f"/api/v1/favorites/{product['id']}", headers=auth(user_token))
        r = client.delete(f"/api/v1/favorites/{product['id']}", headers=auth(user_token))
        assert r.status_code == 200
        r2 = client.get("/api/v1/favorites/", headers=auth(user_token))
        assert r2.json()["total"] == 0

    def test_remove_nonexistent_fails(self, client, user_token, product):
        r = client.delete(f"/api/v1/favorites/{product['id']}", headers=auth(user_token))
        assert r.status_code == 404

    def test_favorites_isolated_per_user(self, client, user_token, product):
        other = register(client, "other")
        client.post(f"/api/v1/favorites/{product['id']}", headers=auth(user_token))
        r = client.get("/api/v1/favorites/", headers=auth(other))
        assert r.json()["total"] == 0

    def test_requires_auth(self, client, product):
        r = client.get("/api/v1/favorites/")
        assert r.status_code == 401
