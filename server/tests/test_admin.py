"""Admin panel — statistika, foydalanuvchilar, buyurtmalar, pul chiqarish."""
from decimal import Decimal
from tests.conftest import register, auth


class TestAdminStats:
    def test_stats_empty(self, client, admin_token):
        r = client.get("/api/v1/admin/stats", headers=auth(admin_token))
        assert r.status_code == 200
        data = r.json()
        assert data["total_users"] >= 1  # admin o'zi
        assert data["total_orders"] == 0
        assert data["open_disputes"] == 0
        assert data["pending_withdrawals"] == 0

    def test_stats_after_order(self, client, admin_token, order):
        r = client.get("/api/v1/admin/stats", headers=auth(admin_token))
        assert r.json()["total_orders"] == 1

    def test_stats_requires_admin(self, client, user_token):
        r = client.get("/api/v1/admin/stats", headers=auth(user_token))
        assert r.status_code == 403

    def test_stats_open_disputes(self, client, admin_token, funded_buyer, order):
        client.post(f"/api/v1/orders/{order['id']}/dispute",
                    json={"order_id": order["id"], "reason": "Sabab"},
                    headers=auth(funded_buyer))
        r = client.get("/api/v1/admin/stats", headers=auth(admin_token))
        assert r.json()["open_disputes"] == 1


class TestAdminUsers:
    def test_list_users(self, client, admin_token, user_token):
        r = client.get("/api/v1/admin/users", headers=auth(admin_token))
        assert r.status_code == 200
        assert r.json()["total"] >= 2  # admin + buyer

    def test_search_users(self, client, admin_token, user_token):
        r = client.get("/api/v1/admin/users?search=buyer1", headers=auth(admin_token))
        assert r.json()["total"] >= 1

    def test_filter_sellers(self, client, admin_token, seller_token):
        r = client.get("/api/v1/admin/users?is_seller=true", headers=auth(admin_token))
        assert r.json()["total"] >= 1

    def test_make_user_admin(self, client, admin_token, user_token, db):
        from app import models
        user = db.query(models.User).filter(models.User.username == "buyer1").first()
        r = client.post(f"/api/v1/admin/users/{user.id}/make-admin", headers=auth(admin_token))
        assert r.status_code == 200
        assert r.json()["is_admin"] is True

    def test_make_user_seller(self, client, admin_token, user_token, db):
        from app import models
        user = db.query(models.User).filter(models.User.username == "buyer1").first()
        r = client.post(f"/api/v1/admin/users/{user.id}/make-seller", headers=auth(admin_token))
        assert r.status_code == 200
        assert r.json()["is_seller"] is True


class TestAdminOrders:
    def test_list_all_orders(self, client, admin_token, order):
        r = client.get("/api/v1/admin/orders", headers=auth(admin_token))
        assert r.json()["total"] == 1

    def test_filter_orders_by_status(self, client, admin_token, order):
        r = client.get("/api/v1/admin/orders?status=PAID_HELD", headers=auth(admin_token))
        assert r.json()["total"] == 1
        r = client.get("/api/v1/admin/orders?status=COMPLETED", headers=auth(admin_token))
        assert r.json()["total"] == 0


class TestAdminWithdrawals:
    def _make_withdrawal(self, client, seller_token, db):
        from app import models
        seller = db.query(models.User).filter(models.User.username == "seller1").first()
        seller.balance = Decimal("100000.00")
        db.commit()
        r = client.post("/api/v1/withdrawals/", json={
            "amount": "50000.00", "address": "9860001234567890",
            "payment_method": "Click",
        }, headers=auth(seller_token))
        return r.json()

    def test_list_withdrawals(self, client, admin_token, seller_token, db):
        self._make_withdrawal(client, seller_token, db)
        r = client.get("/api/v1/admin/withdrawals", headers=auth(admin_token))
        assert r.json()["total"] == 1

    def test_approve_withdrawal(self, client, admin_token, seller_token, db):
        wr = self._make_withdrawal(client, seller_token, db)
        r = client.post(f"/api/v1/admin/withdrawals/{wr['id']}/process",
                        json={"status": "APPROVED"},
                        headers=auth(admin_token))
        assert r.status_code == 200
        assert r.json()["status"] == "APPROVED"
        from app import models
        seller = db.query(models.User).filter(models.User.username == "seller1").first()
        assert seller.balance == Decimal("50000.00")

    def test_reject_withdrawal(self, client, admin_token, seller_token, db):
        wr = self._make_withdrawal(client, seller_token, db)
        r = client.post(f"/api/v1/admin/withdrawals/{wr['id']}/process",
                        json={"status": "REJECTED", "admin_note": "Noto'g'ri karta"},
                        headers=auth(admin_token))
        assert r.status_code == 200
        assert r.json()["status"] == "REJECTED"
        assert r.json()["admin_note"] == "Noto'g'ri karta"
        from app import models
        seller = db.query(models.User).filter(models.User.username == "seller1").first()
        assert seller.balance == Decimal("100000.00")  # Pul qaytarilmadi (hech qachon chiqmagan)

    def test_double_process_fails(self, client, admin_token, seller_token, db):
        wr = self._make_withdrawal(client, seller_token, db)
        client.post(f"/api/v1/admin/withdrawals/{wr['id']}/process",
                    json={"status": "APPROVED"}, headers=auth(admin_token))
        r = client.post(f"/api/v1/admin/withdrawals/{wr['id']}/process",
                        json={"status": "REJECTED"}, headers=auth(admin_token))
        assert r.status_code == 400


class TestAdminGameManagement:
    def test_create_category(self, client, admin_token):
        r = client.post("/api/v1/admin/categories",
                        json={"name": "Mobile", "slug": "mobile"},
                        headers=auth(admin_token))
        assert r.status_code == 201

    def test_create_game(self, client, admin_token, category):
        r = client.post("/api/v1/admin/games", json={
            "name": "PUBG", "slug": "pubg", "category_id": category["id"],
        }, headers=auth(admin_token))
        assert r.status_code == 201

    def test_create_subcategory(self, client, admin_token, game):
        r = client.post("/api/v1/admin/subcategories", json={
            "name": "UC", "slug": "uc", "game_id": game["id"],
        }, headers=auth(admin_token))
        assert r.status_code == 201


class TestAdminHighlight:
    def test_highlight_product(self, client, admin_token, product):
        r = client.post(f"/api/v1/admin/products/{product['id']}/highlight",
                        params={"highlight": True},
                        headers=auth(admin_token))
        assert r.status_code == 200

    def test_unhighlight_product(self, client, admin_token, product):
        r = client.post(f"/api/v1/admin/products/{product['id']}/highlight",
                        params={"highlight": False},
                        headers=auth(admin_token))
        assert r.status_code == 200
