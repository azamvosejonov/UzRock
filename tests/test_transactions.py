"""Tranzaksiyalar tarixi."""
from decimal import Decimal
from tests.conftest import register, auth
from app import models


class TestTransactions:
    def test_list_empty(self, client, user_token):
        r = client.get("/api/v1/transactions/", headers=auth(user_token))
        assert r.status_code == 200
        assert r.json()["total"] == 0

    def test_payment_hold_recorded(self, client, funded_buyer, order, db):
        txs = db.query(models.Transaction).filter(models.Transaction.type == "PAYMENT_HOLD").all()
        assert len(txs) == 1
        assert txs[0].amount == Decimal("10.00")

    def test_payment_release_recorded(self, client, funded_buyer, completed_order, db):
        txs = db.query(models.Transaction).filter(models.Transaction.type == "PAYMENT_RELEASE").all()
        assert len(txs) == 1
        assert txs[0].amount == Decimal("9.50")  # 5% komissiya olib tashlandi

    def test_refund_recorded_on_cancel(self, client, funded_buyer, order, db):
        client.post(f"/api/v1/orders/{order['id']}/cancel", headers=auth(funded_buyer))
        txs = db.query(models.Transaction).filter(models.Transaction.type == "REFUND").all()
        assert len(txs) == 1
        assert txs[0].amount == Decimal("10.00")

    def test_filter_by_type(self, client, funded_buyer, order, db):
        r = client.get("/api/v1/transactions/?tx_type=PAYMENT_HOLD", headers=auth(funded_buyer))
        assert r.json()["total"] == 1
        r = client.get("/api/v1/transactions/?tx_type=DEPOSIT", headers=auth(funded_buyer))
        assert r.json()["total"] == 0

    def test_requires_auth(self, client):
        r = client.get("/api/v1/transactions/")
        assert r.status_code == 403
