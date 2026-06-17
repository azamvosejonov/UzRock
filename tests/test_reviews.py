"""Baholar — yaratish, javob berish, reyting hisoblash."""
from tests.conftest import register, auth


class TestReviewCreate:
    def test_create_review_after_completion(self, client, funded_buyer, completed_order, product):
        r = client.post(
            "/api/v1/reviews/",
            params={"order_id": completed_order["id"]},
            json={"rating": 5, "comment": "Zo'r!"},
            headers=auth(funded_buyer),
        )
        assert r.status_code == 201
        data = r.json()
        assert data["rating"] == 5
        assert data["comment"] == "Zo'r!"

    def test_cannot_review_incomplete_order(self, client, funded_buyer, order):
        r = client.post(
            "/api/v1/reviews/",
            params={"order_id": order["id"]},
            json={"rating": 3},
            headers=auth(funded_buyer),
        )
        assert r.status_code == 400

    def test_seller_cannot_review(self, client, seller_token, completed_order):
        r = client.post(
            "/api/v1/reviews/",
            params={"order_id": completed_order["id"]},
            json={"rating": 1},
            headers=auth(seller_token),
        )
        assert r.status_code == 403

    def test_create_review_invalid_rating_low(self, client, funded_buyer, completed_order):
        r = client.post(
            "/api/v1/reviews/",
            params={"order_id": completed_order["id"]},
            json={"rating": 0},
            headers=auth(funded_buyer),
        )
        assert r.status_code == 422

    def test_create_review_invalid_rating_high(self, client, funded_buyer, completed_order):
        r = client.post(
            "/api/v1/reviews/",
            params={"order_id": completed_order["id"]},
            json={"rating": 6},
            headers=auth(funded_buyer),
        )
        assert r.status_code == 422

    def test_duplicate_review_fails(self, client, funded_buyer, completed_order):
        client.post(
            "/api/v1/reviews/",
            params={"order_id": completed_order["id"]},
            json={"rating": 5},
            headers=auth(funded_buyer),
        )
        r = client.post(
            "/api/v1/reviews/",
            params={"order_id": completed_order["id"]},
            json={"rating": 4},
            headers=auth(funded_buyer),
        )
        assert r.status_code == 409

    def test_seller_rating_updated(self, client, funded_buyer, completed_order, db):
        from app import models
        client.post(
            "/api/v1/reviews/",
            params={"order_id": completed_order["id"]},
            json={"rating": 4},
            headers=auth(funded_buyer),
        )
        seller = db.query(models.User).filter(models.User.username == "seller1").first()
        assert seller.rating == 4.0

    def test_product_review_count_updated(self, client, funded_buyer, completed_order, product, db):
        from app import models
        client.post(
            "/api/v1/reviews/",
            params={"order_id": completed_order["id"]},
            json={"rating": 5},
            headers=auth(funded_buyer),
        )
        p = db.query(models.Product).filter(models.Product.id == product["id"]).first()
        assert p.review_count == 1


class TestReviewList:
    def test_list_reviews(self, client, funded_buyer, completed_order):
        client.post(
            "/api/v1/reviews/",
            params={"order_id": completed_order["id"]},
            json={"rating": 4},
            headers=auth(funded_buyer),
        )
        r = client.get("/api/v1/reviews/")
        assert r.json()["total"] == 1

    def test_filter_reviews_by_rating(self, client, funded_buyer, completed_order):
        client.post(
            "/api/v1/reviews/",
            params={"order_id": completed_order["id"]},
            json={"rating": 5},
            headers=auth(funded_buyer),
        )
        r = client.get("/api/v1/reviews/?rating=5")
        assert r.json()["total"] == 1
        r = client.get("/api/v1/reviews/?rating=3")
        assert r.json()["total"] == 0


class TestReviewReply:
    def test_seller_replies_to_review(self, client, seller_token, funded_buyer, completed_order):
        review_r = client.post(
            "/api/v1/reviews/",
            params={"order_id": completed_order["id"]},
            json={"rating": 3, "comment": "OK"},
            headers=auth(funded_buyer),
        )
        review_id = review_r.json()["id"]
        r = client.post(
            f"/api/v1/reviews/{review_id}/reply",
            json={"reply": "Rahmat!"},
            headers=auth(seller_token),
        )
        assert r.status_code == 200
        assert r.json()["reply"] == "Rahmat!"

    def test_buyer_cannot_reply(self, client, funded_buyer, seller_token, completed_order):
        review_r = client.post(
            "/api/v1/reviews/",
            params={"order_id": completed_order["id"]},
            json={"rating": 5},
            headers=auth(funded_buyer),
        )
        r = client.post(
            f"/api/v1/reviews/{review_r.json()['id']}/reply",
            json={"reply": "Hack"},
            headers=auth(funded_buyer),
        )
        assert r.status_code == 403

    def test_double_reply_fails(self, client, seller_token, funded_buyer, completed_order):
        review_r = client.post(
            "/api/v1/reviews/",
            params={"order_id": completed_order["id"]},
            json={"rating": 4},
            headers=auth(funded_buyer),
        )
        rid = review_r.json()["id"]
        client.post(f"/api/v1/reviews/{rid}/reply", json={"reply": "1"}, headers=auth(seller_token))
        r = client.post(f"/api/v1/reviews/{rid}/reply", json={"reply": "2"}, headers=auth(seller_token))
        assert r.status_code == 400
