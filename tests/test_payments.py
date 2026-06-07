"""To'lov tizimi — Click va Payme."""
import base64
import hashlib
from tests.conftest import register, auth, click_sign


CLICK_SERVICE_ID = "12345"
CLICK_SECRET = "test_click_secret"


def _click_payload(merchant_trans_id, amount=100.0, action=0, error=0):
    sign_time = "2024-01-01 10:00:00"
    trans_id = 99001
    sign = click_sign(trans_id, CLICK_SERVICE_ID, CLICK_SECRET,
                      merchant_trans_id, amount, action, sign_time)
    return {
        "click_trans_id": trans_id,
        "service_id": int(CLICK_SERVICE_ID),
        "click_paydoc_id": 12345,
        "merchant_trans_id": merchant_trans_id,
        "amount": amount,
        "action": action,
        "error": error,
        "error_note": "Success",
        "sign_time": sign_time,
        "sign_string": sign,
    }


def _payme_headers():
    creds = base64.b64encode(b"test_payme_id:test_payme_key").decode()
    return {"Authorization": f"Basic {creds}"}


class TestTopup:
    def test_topup_click(self, client, user_token):
        r = client.post("/api/v1/payments/topup",
                        params={"amount": "50000", "method": "click"},
                        headers=auth(user_token))
        assert r.status_code == 200
        data = r.json()
        assert "payment_url" in data
        assert "click" in data["payment_url"]

    def test_topup_payme(self, client, user_token):
        r = client.post("/api/v1/payments/topup",
                        params={"amount": "30000", "method": "payme"},
                        headers=auth(user_token))
        assert r.status_code == 200
        assert "paycom" in r.json()["payment_url"]

    def test_topup_invalid_method(self, client, user_token):
        r = client.post("/api/v1/payments/topup",
                        params={"amount": "1000", "method": "cash"},
                        headers=auth(user_token))
        assert r.status_code == 400

    def test_topup_requires_auth(self, client):
        r = client.post("/api/v1/payments/topup", params={"amount": "1000", "method": "click"})
        assert r.status_code == 403


class TestClickPrepare:
    def test_prepare_valid(self, client, db):
        from app import models
        user = models.User(username="cu", email="cu@test.uz", password_hash="h")
        db.add(user)
        db.commit()
        merchant_id = f"topup_{user.id}_1000"
        payload = _click_payload(merchant_id, amount=1000.0, action=0)
        r = client.post("/api/v1/payments/click/prepare", json=payload)
        assert r.status_code == 200
        data = r.json()
        assert data["error"] == 0

    def test_prepare_invalid_signature(self, client, db):
        from app import models
        user = models.User(username="cu2", email="cu2@test.uz", password_hash="h")
        db.add(user)
        db.commit()
        merchant_id = f"topup_{user.id}_500"
        payload = _click_payload(merchant_id)
        payload["sign_string"] = "wrong_signature"
        r = client.post("/api/v1/payments/click/prepare", json=payload)
        assert r.json()["error"] == -1

    def test_prepare_user_not_found(self, client):
        merchant_id = "topup_00000000-0000-0000-0000-000000000000_1000"
        payload = _click_payload(merchant_id)
        r = client.post("/api/v1/payments/click/prepare", json=payload)
        assert r.json()["error"] != 0


class TestClickComplete:
    def test_complete_adds_balance(self, client, db):
        from app import models
        user = models.User(username="cu3", email="cu3@test.uz", password_hash="h")
        db.add(user)
        db.commit()
        merchant_id = f"topup_{user.id}_5000"
        payload = _click_payload(merchant_id, amount=5000.0, action=1)
        r = client.post("/api/v1/payments/click/complete", json=payload)
        assert r.status_code == 200
        assert r.json()["error"] == 0
        db.refresh(user)
        from decimal import Decimal
        assert user.balance == Decimal("5000.00")

    def test_complete_invalid_sign(self, client, db):
        from app import models
        user = models.User(username="cu4", email="cu4@test.uz", password_hash="h")
        db.add(user)
        db.commit()
        payload = _click_payload(f"topup_{user.id}_1000", action=1)
        payload["sign_string"] = "bad"
        r = client.post("/api/v1/payments/click/complete", json=payload)
        assert r.json()["error"] == -1


class TestPayme:
    def test_check_perform_valid(self, client, db):
        from app import models
        user = models.User(username="pu1", email="pu1@test.uz", password_hash="h")
        db.add(user)
        db.commit()
        r = client.post("/api/v1/payments/payme", json={
            "method": "CheckPerformTransaction",
            "params": {
                "amount": 500000,
                "account": {"merchant_trans_id": f"topup_{user.id}_5000"},
            },
            "id": 1,
        }, headers=_payme_headers())
        assert r.status_code == 200
        assert r.json()["result"]["allow"] is True

    def test_check_perform_user_not_found(self, client):
        r = client.post("/api/v1/payments/payme", json={
            "method": "CheckPerformTransaction",
            "params": {
                "amount": 100000,
                "account": {"merchant_trans_id": "topup_00000000-0000-0000-0000-000000000000_1000"},
            },
            "id": 2,
        }, headers=_payme_headers())
        assert "error" in r.json()

    def test_create_transaction(self, client, db):
        from app import models
        user = models.User(username="pu2", email="pu2@test.uz", password_hash="h")
        db.add(user)
        db.commit()
        r = client.post("/api/v1/payments/payme", json={
            "method": "CreateTransaction",
            "params": {
                "id": "payme_tx_123",
                "time": 1234567890,
                "amount": 200000,
                "account": {"merchant_trans_id": f"topup_{user.id}_2000"},
            },
            "id": 3,
        }, headers=_payme_headers())
        assert r.status_code == 200
        assert r.json()["result"]["state"] == 1

    def test_perform_transaction_adds_balance(self, client, db):
        from app import models
        from decimal import Decimal
        user = models.User(username="pu3", email="pu3@test.uz", password_hash="h")
        db.add(user)
        db.commit()
        r = client.post("/api/v1/payments/payme", json={
            "method": "PerformTransaction",
            "params": {
                "id": "payme_tx_456",
                "account": {"merchant_trans_id": f"topup_{user.id}_1000"},
                "amount": 100000,
            },
            "id": 4,
        }, headers=_payme_headers())
        assert r.status_code == 200
        assert r.json()["result"]["state"] == 2
        db.refresh(user)
        assert user.balance == Decimal("1000.00")

    def test_cancel_transaction(self, client):
        r = client.post("/api/v1/payments/payme", json={
            "method": "CancelTransaction",
            "params": {"id": "tx_to_cancel", "reason": 1},
            "id": 5,
        }, headers=_payme_headers())
        assert r.json()["result"]["state"] == -1

    def test_payme_requires_auth(self, client):
        r = client.post("/api/v1/payments/payme", json={
            "method": "CheckPerformTransaction",
            "params": {"amount": 1000, "account": {}},
            "id": 1,
        })
        assert r.status_code == 401
