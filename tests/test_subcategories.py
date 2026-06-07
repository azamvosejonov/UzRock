"""Subkategoriyalar."""
from tests.conftest import register, auth


class TestSubcategories:
    def test_list_empty(self, client):
        r = client.get("/api/v1/subcategories/")
        assert r.json() == []

    def test_list_by_game(self, client, subcategory, game):
        r = client.get(f"/api/v1/subcategories/?game_id={game['id']}")
        assert len(r.json()) == 1

    def test_create_by_admin(self, client, admin_token, game):
        r = client.post("/api/v1/subcategories/", json={
            "name": "Accounts", "slug": "accounts", "game_id": game["id"],
        }, headers=auth(admin_token))
        assert r.status_code == 201

    def test_create_by_user_fails(self, client, user_token, game):
        r = client.post("/api/v1/subcategories/", json={
            "name": "Test", "slug": "test", "game_id": game["id"],
        }, headers=auth(user_token))
        assert r.status_code == 403

    def test_delete_by_admin(self, client, admin_token, subcategory):
        r = client.delete(f"/api/v1/subcategories/{subcategory['id']}", headers=auth(admin_token))
        assert r.status_code == 204

    def test_delete_nonexistent(self, client, admin_token):
        import uuid
        r = client.delete(f"/api/v1/subcategories/{uuid.uuid4()}", headers=auth(admin_token))
        assert r.status_code == 404
