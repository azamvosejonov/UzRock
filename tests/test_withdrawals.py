"""Pul chiqarish so'rovlari."""
from decimal import Decimal
from tests.conftest import register, auth


class TestWithdrawals:
    def test_create_withdrawal(self, client, seller_token, db):
        from app import models
        seller = db.query(models.User).filter(models.User.username == "seller1").first()
        seller.balance = Decimal("50000.00")
        db.commit()
        r = client.post("/api/v1/withdrawals/", json={
            "amount": "30000.00",
            "address": "9860001234567890",
            "payment_method": "Click",
        }, headers=auth(seller_token))
        assert r.status_code == 201
        data = r.json()
        assert data["status"] == "PENDING"
        assert float(data["amount"]) == 30000.00

    def test_non_seller_cannot_withdraw(self, client, user_token, db):
        from app import models
        user = db.query(models.User).filter(models.User.username == "buyer1").first()
        user.balance = Decimal("100000.00")
        db.commit()
        r = client.post("/api/v1/withdrawals/", json={
            "amount": "50000.00", "address": "1234", "payment_method": "Click",
        }, headers=auth(user_token))
        assert r.status_code == 403

    def test_insufficient_balance(self, client, seller_token):
        r = client.post("/api/v1/withdrawals/", json={
            "amount": "50000.00", "address": "1234", "payment_method": "Click",
        }, headers=auth(seller_token))
        assert r.status_code == 400

    def test_below_minimum(self, client, seller_token, db):
        from app import models
        seller = db.query(models.User).filter(models.User.username == "seller1").first()
        seller.balance = Decimal("5000.00")
        db.commit()
        r = client.post("/api/v1/withdrawals/", json={
            "amount": "5000.00", "address": "1234", "payment_method": "Click",
        }, headers=auth(seller_token))
        assert r.status_code == 400
        assert "minimal" in r.json()["detail"].lower()

    def test_list_my_withdrawals(self, client, seller_token, db):
        from app import models
        seller = db.query(models.User).filter(models.User.username == "seller1").first()
        seller.balance = Decimal("100000.00")
        db.commit()
        client.post("/api/v1/withdrawals/", json={
            "amount": "20000.00", "address": "1234", "payment_method": "Click",
        }, headers=auth(seller_token))
        r = client.get("/api/v1/withdrawals/", headers=auth(seller_token))
        assert r.json()["total"] == 1

    def test_requires_auth(self, client):
        r = client.get("/api/v1/withdrawals/")
        assert r.status_code == 401
