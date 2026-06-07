"""Nizolar — ochish va admin tomonidan hal qilish."""
from decimal import Decimal
from tests.conftest import register, auth


def _open_dispute(client, funded_buyer, order):
    return client.post(
        f"/api/v1/orders/{order['id']}/dispute",
        json={"order_id": order["id"], "reason": "Tovar kelmadi"},
        headers=auth(funded_buyer),
    )


class TestDisputeList:
    def test_admin_can_list(self, client, admin_token, funded_buyer, order):
        _open_dispute(client, funded_buyer, order)
        r = client.get("/api/v1/disputes/", headers=auth(admin_token))
        assert r.status_code == 200
        assert r.json()["total"] == 1

    def test_user_cannot_list_all(self, client, user_token):
        r = client.get("/api/v1/disputes/", headers=auth(user_token))
        assert r.status_code == 403

    def test_my_disputes(self, client, funded_buyer, order):
        _open_dispute(client, funded_buyer, order)
        r = client.get("/api/v1/disputes/my", headers=auth(funded_buyer))
        assert r.json()["total"] == 1

    def test_filter_by_status(self, client, admin_token, funded_buyer, order):
        _open_dispute(client, funded_buyer, order)
        r = client.get("/api/v1/disputes/?status=OPEN", headers=auth(admin_token))
        assert r.json()["total"] == 1
        r = client.get("/api/v1/disputes/?status=RESOLVED_BUYER", headers=auth(admin_token))
        assert r.json()["total"] == 0


class TestDisputeResolve:
    def test_resolve_for_buyer(self, client, admin_token, funded_buyer, order, db):
        from app import models
        _open_dispute(client, funded_buyer, order)
        dispute_r = client.get("/api/v1/disputes/", headers=auth(admin_token))
        did = dispute_r.json()["items"][0]["id"]
        r = client.post(f"/api/v1/disputes/{did}/resolve",
                        json={"winner": "buyer", "resolution_note": "Sotuvchi tovarni yetkazmagan"},
                        headers=auth(admin_token))
        assert r.status_code == 200
        assert r.json()["status"] == "RESOLVED_BUYER"
        buyer = db.query(models.User).filter(models.User.username == "buyer_rich").first()
        assert buyer.balance == Decimal("100.00")
        assert buyer.held_balance == Decimal("0.00")

    def test_resolve_for_seller(self, client, admin_token, funded_buyer, seller_token, order, db):
        from app import models
        _open_dispute(client, funded_buyer, order)
        dispute_r = client.get("/api/v1/disputes/", headers=auth(admin_token))
        did = dispute_r.json()["items"][0]["id"]
        r = client.post(f"/api/v1/disputes/{did}/resolve",
                        json={"winner": "seller", "resolution_note": "Xaridor noto'g'ri"},
                        headers=auth(admin_token))
        assert r.status_code == 200
        assert r.json()["status"] == "RESOLVED_SELLER"
        seller = db.query(models.User).filter(models.User.username == "seller1").first()
        assert seller.balance == Decimal("10.00")

    def test_cannot_resolve_twice(self, client, admin_token, funded_buyer, order):
        _open_dispute(client, funded_buyer, order)
        disputes = client.get("/api/v1/disputes/", headers=auth(admin_token)).json()["items"]
        did = disputes[0]["id"]
        client.post(f"/api/v1/disputes/{did}/resolve",
                    json={"winner": "buyer", "resolution_note": "OK"},
                    headers=auth(admin_token))
        r = client.post(f"/api/v1/disputes/{did}/resolve",
                        json={"winner": "seller", "resolution_note": "Again"},
                        headers=auth(admin_token))
        assert r.status_code == 400

    def test_non_admin_cannot_resolve(self, client, user_token, funded_buyer, order):
        _open_dispute(client, funded_buyer, order)
        r = client.post(f"/api/v1/disputes/some-id/resolve",
                        json={"winner": "buyer", "resolution_note": "Hack"},
                        headers=auth(user_token))
        assert r.status_code == 403
