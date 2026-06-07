"""Foydalanuvchi public profili."""
from tests.conftest import register, auth


class TestUserProfile:
    def test_get_public_profile(self, client, user_token):
        r = client.get("/api/v1/users/buyer1")
        assert r.status_code == 200
        data = r.json()
        assert data["username"] == "buyer1"
        assert "email" not in data
        assert "balance" not in data
        assert "password_hash" not in data

    def test_get_nonexistent_user(self, client):
        r = client.get("/api/v1/users/ghost_user_xyz")
        assert r.status_code == 404

    def test_seller_products_visible(self, client, seller_token, product):
        r = client.get("/api/v1/users/seller1/products")
        assert r.status_code == 200
        assert r.json()["total"] == 1

    def test_seller_products_no_inactive(self, client, seller_token, product):
        client.delete(f"/api/v1/products/{product['id']}", headers=auth(seller_token))
        r = client.get("/api/v1/users/seller1/products")
        assert r.json()["total"] == 0

    def test_seller_reviews_visible(self, client, funded_buyer, completed_order, seller_token):
        client.post(
            "/api/v1/reviews/",
            params={"order_id": completed_order["id"]},
            json={"rating": 5, "comment": "Zo'r!"},
            headers=auth(funded_buyer),
        )
        r = client.get("/api/v1/users/seller1/reviews")
        assert r.json()["total"] == 1

    def test_pagination_products(self, client, seller_token, game, subcategory):
        for i in range(5):
            client.post("/api/v1/products/", json={
                "title": f"P{i}", "price": "10.00",
                "game_id": game["id"],
                "subcategory_id": subcategory["id"],
                "is_auto_delivery": True,
            }, headers=auth(seller_token))
        r = client.get("/api/v1/users/seller1/products?page=1&size=3")
        assert len(r.json()["items"]) == 3
        assert r.json()["pages"] == 2
