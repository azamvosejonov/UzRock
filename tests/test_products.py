"""Mahsulotlar — CRUD, filterlar, sort, bump, rasmlar."""
from tests.conftest import register, auth


class TestProductList:
    def test_list_empty(self, client):
        r = client.get("/api/v1/products/")
        assert r.status_code == 200
        assert r.json()["total"] == 0

    def test_list_returns_product(self, client, product):
        r = client.get("/api/v1/products/")
        assert r.status_code == 200
        assert r.json()["total"] == 1

    def test_filter_by_game_id(self, client, product, game):
        r = client.get(f"/api/v1/products/?game_id={game['id']}")
        assert r.json()["total"] == 1

    def test_filter_by_wrong_game_id(self, client, product):
        import uuid
        r = client.get(f"/api/v1/products/?game_id={uuid.uuid4()}")
        assert r.json()["total"] == 0

    def test_filter_by_subcategory(self, client, product, subcategory):
        r = client.get(f"/api/v1/products/?subcategory_id={subcategory['id']}")
        assert r.json()["total"] == 1

    def test_filter_min_price(self, client, product):
        r = client.get("/api/v1/products/?min_price=5")
        assert r.json()["total"] == 1
        r = client.get("/api/v1/products/?min_price=20")
        assert r.json()["total"] == 0

    def test_filter_max_price(self, client, product):
        r = client.get("/api/v1/products/?max_price=20")
        assert r.json()["total"] == 1
        r = client.get("/api/v1/products/?max_price=5")
        assert r.json()["total"] == 0

    def test_filter_is_auto_delivery(self, client, product):
        r = client.get("/api/v1/products/?is_auto_delivery=true")
        assert r.json()["total"] == 1
        r = client.get("/api/v1/products/?is_auto_delivery=false")
        assert r.json()["total"] == 0

    def test_filter_has_discount(self, client, seller_token, game, subcategory):
        client.post("/api/v1/products/", json={
            "title": "Discounted", "price": "8.00", "original_price": "10.00",
            "discount_percent": 20,
            "game_id": game["id"], "subcategory_id": subcategory["id"],
            "is_auto_delivery": False,
        }, headers=auth(seller_token))
        r = client.get("/api/v1/products/?has_discount=true")
        assert r.json()["total"] == 1

    def test_search_by_title(self, client, product):
        r = client.get("/api/v1/products/?search=Robux")
        assert r.json()["total"] == 1
        r = client.get("/api/v1/products/?search=Nonexistent")
        assert r.json()["total"] == 0

    def test_sort_price_asc(self, client, seller_token, game, subcategory):
        for price in ["5.00", "15.00", "10.00"]:
            client.post("/api/v1/products/", json={
                "title": f"P{price}", "price": price,
                "game_id": game["id"], "subcategory_id": subcategory["id"],
                "is_auto_delivery": True,
            }, headers=auth(seller_token))
        r = client.get("/api/v1/products/?sort_by=price_asc")
        prices = [float(item["price"]) for item in r.json()["items"]]
        assert prices == sorted(prices)

    def test_sort_price_desc(self, client, seller_token, game, subcategory):
        for price in ["5.00", "15.00", "10.00"]:
            client.post("/api/v1/products/", json={
                "title": f"P{price}", "price": price,
                "game_id": game["id"], "subcategory_id": subcategory["id"],
                "is_auto_delivery": True,
            }, headers=auth(seller_token))
        r = client.get("/api/v1/products/?sort_by=price_desc")
        prices = [float(item["price"]) for item in r.json()["items"]]
        assert prices == sorted(prices, reverse=True)

    def test_pagination(self, client, seller_token, game, subcategory):
        for i in range(5):
            client.post("/api/v1/products/", json={
                "title": f"P{i}", "price": "10.00",
                "game_id": game["id"], "subcategory_id": subcategory["id"],
                "is_auto_delivery": True,
            }, headers=auth(seller_token))
        r = client.get("/api/v1/products/?page=1&size=3")
        data = r.json()
        assert len(data["items"]) == 3
        assert data["total"] == 5
        assert data["pages"] == 2


class TestProductGet:
    def test_get_product(self, client, product):
        r = client.get(f"/api/v1/products/{product['id']}")
        assert r.status_code == 200
        assert r.json()["title"] == "100 Robux"

    def test_get_product_increments_views(self, client, product):
        client.get(f"/api/v1/products/{product['id']}")
        r = client.get(f"/api/v1/products/{product['id']}")
        assert r.json()["views"] == 2

    def test_get_nonexistent_product(self, client):
        import uuid
        r = client.get(f"/api/v1/products/{uuid.uuid4()}")
        assert r.status_code == 404


class TestProductCreate:
    def test_create_product_as_seller(self, client, seller_token, game, subcategory):
        r = client.post("/api/v1/products/", json={
            "title": "500 Robux", "price": "25.00",
            "game_id": game["id"], "subcategory_id": subcategory["id"],
            "is_auto_delivery": True,
        }, headers=auth(seller_token))
        assert r.status_code == 201
        assert r.json()["title"] == "500 Robux"

    def test_create_product_as_buyer_fails(self, client, user_token, game, subcategory):
        r = client.post("/api/v1/products/", json={
            "title": "Test", "price": "10.00",
            "game_id": game["id"], "subcategory_id": subcategory["id"],
            "is_auto_delivery": False,
        }, headers=auth(user_token))
        assert r.status_code == 403

    def test_create_product_with_jsonb_attributes(self, client, seller_token, game, subcategory):
        r = client.post("/api/v1/products/", json={
            "title": "PC Game", "price": "50.00",
            "game_id": game["id"], "subcategory_id": subcategory["id"],
            "is_auto_delivery": False,
            "dynamic_attributes": {"platform": "PC", "region": "Global"},
        }, headers=auth(seller_token))
        assert r.status_code == 201
        assert r.json()["dynamic_attributes"]["platform"] == "PC"

    def test_create_product_missing_fields(self, client, seller_token, game, subcategory):
        # Title is required, leaving it out (incomplete data)
        r = client.post("/api/v1/products/", json={
            "price": "25.00",
            "game_id": game["id"], "subcategory_id": subcategory["id"],
            "is_auto_delivery": True,
        }, headers=auth(seller_token))
        assert r.status_code == 422

    def test_create_product_invalid_price(self, client, seller_token, game, subcategory):
        # Price must be > 0 (invalid/wrong data)
        r = client.post("/api/v1/products/", json={
            "title": "Invalid Price Game", "price": "0.00",
            "game_id": game["id"], "subcategory_id": subcategory["id"],
            "is_auto_delivery": True,
        }, headers=auth(seller_token))
        assert r.status_code == 422


class TestProductUpdate:
    def test_update_own_product(self, client, seller_token, product):
        r = client.patch(f"/api/v1/products/{product['id']}",
                         json={"title": "Updated Title", "price": "15.00",
                               "game_id": product["game_id"],
                               "subcategory_id": product["subcategory_id"],
                               "is_auto_delivery": True},
                         headers=auth(seller_token))
        assert r.status_code == 200
        assert r.json()["title"] == "Updated Title"

    def test_update_others_product_fails(self, client, product):
        other = register(client, "other_seller")
        client.post("/api/v1/auth/me/become-seller", headers=auth(other))
        r = client.patch(f"/api/v1/products/{product['id']}",
                         json={"title": "Hack", "price": "1.00",
                               "game_id": product["game_id"],
                               "subcategory_id": product["subcategory_id"],
                               "is_auto_delivery": True},
                         headers=auth(other))
        assert r.status_code == 403


class TestProductDelete:
    def test_soft_delete(self, client, seller_token, product):
        r = client.delete(f"/api/v1/products/{product['id']}", headers=auth(seller_token))
        assert r.status_code == 200
        r2 = client.get(f"/api/v1/products/{product['id']}")
        assert r2.status_code == 404


class TestProductBump:
    def test_bump_product(self, client, seller_token, product):
        r = client.post(f"/api/v1/products/{product['id']}/bump", headers=auth(seller_token))
        assert r.status_code == 200

    def test_bump_others_product_fails(self, client, product, user_token):
        r = client.post(f"/api/v1/products/{product['id']}/bump", headers=auth(user_token))
        assert r.status_code == 403


class TestProductImages:
    def test_add_image(self, client, seller_token, product):
        r = client.post(
            f"/api/v1/products/{product['id']}/images",
            params={"image_url": "https://img.test/pic.jpg", "sort_order": 0},
            headers=auth(seller_token),
        )
        assert r.status_code == 201
        assert r.json()["image_url"] == "https://img.test/pic.jpg"

    def test_delete_image(self, client, seller_token, product):
        r = client.post(
            f"/api/v1/products/{product['id']}/images",
            params={"image_url": "https://img.test/pic.jpg"},
            headers=auth(seller_token),
        )
        img_id = r.json()["id"]
        r2 = client.delete(
            f"/api/v1/products/{product['id']}/images/{img_id}",
            headers=auth(seller_token),
        )
        assert r2.status_code == 200


class TestMyProducts:
    def test_my_products(self, client, seller_token, product):
        r = client.get("/api/v1/products/my", headers=auth(seller_token))
        assert r.status_code == 200
        assert r.json()["total"] == 1

    def test_my_products_requires_seller(self, client, user_token):
        r = client.get("/api/v1/products/my", headers=auth(user_token))
        assert r.status_code == 403
