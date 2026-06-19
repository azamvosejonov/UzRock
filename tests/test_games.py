"""O'yinlar — CRUD va filterlar."""
import uuid
from tests.conftest import register, auth


class TestGameList:
    def test_list_empty(self, client):
        r = client.get("/api/v1/games/")
        assert r.status_code == 200
        assert r.json() == []

    def test_list_with_game(self, client, game):
        r = client.get("/api/v1/games/")
        assert len(r.json()) == 1

    def test_filter_by_category_id(self, client, game, category):
        r = client.get(f"/api/v1/games/?category_id={category['id']}")
        assert len(r.json()) == 1
        r = client.get(f"/api/v1/games/?category_id={uuid.uuid4()}")
        assert r.json() == []

    def test_search_by_name(self, client, game):
        r = client.get("/api/v1/games/?search=Roblox")
        assert len(r.json()) == 1
        r = client.get("/api/v1/games/?search=Minecraft")
        assert r.json() == []


class TestGameGet:
    def test_get_by_slug(self, client, game):
        r = client.get(f"/api/v1/games/{game['slug']}")
        assert r.status_code == 200
        assert r.json()["name"] == "Roblox"

    def test_get_nonexistent(self, client):
        r = client.get("/api/v1/games/no-such-game")
        assert r.status_code == 404

    def test_get_subcategories(self, client, game, subcategory):
        r = client.get(f"/api/v1/games/{game['slug']}/subcategories")
        assert r.status_code == 200
        assert len(r.json()) == 1
        assert r.json()[0]["name"] == "Robux"


class TestGameCreate:
    def test_create_by_admin(self, client, admin_token, category):
        r = client.post("/api/v1/games/", json={
            "name": "Minecraft", "slug": "minecraft",
            "category_id": category["id"],
        }, headers=auth(admin_token))
        assert r.status_code == 201
        assert r.json()["name"] == "Minecraft"

    def test_create_by_user_fails(self, client, user_token, category):
        r = client.post("/api/v1/games/", json={
            "name": "MC", "slug": "mc", "category_id": category["id"],
        }, headers=auth(user_token))
        assert r.status_code == 403

    def test_duplicate_slug_fails(self, client, admin_token, game, category):
        r = client.post("/api/v1/games/", json={
            "name": "Dup", "slug": "roblox", "category_id": category["id"],
        }, headers=auth(admin_token))
        assert r.status_code == 409


class TestGameDelete:
    def test_delete_by_admin(self, client, admin_token, game):
        r = client.delete(f"/api/v1/games/{game['slug']}", headers=auth(admin_token))
        assert r.status_code == 204

    def test_delete_by_user_fails(self, client, user_token, game):
        r = client.delete(f"/api/v1/games/{game['slug']}", headers=auth(user_token))
        assert r.status_code == 403
