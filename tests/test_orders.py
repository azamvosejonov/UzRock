"""
Buyurtmalar — to'liq Escrow flow:
PAID_HELD → DELIVERED → COMPLETED
va bekor qilish, nizo ochish.
"""
from decimal import Decimal
from tests.conftest import register, auth


class TestOrderCreate:
    def test_create_order_success(self, client, funded_buyer, product):
        r = client.post("/api/v1/orders/",
                        json={"product_id": product["id"]},
                        headers=auth(funded_buyer))
        assert r.status_code == 201
        data = r.json()
        assert data["status"] == "PAID_HELD"
        assert float(data["amount"]) == 10.00

    def test_create_order_insufficient_balance(self, client, user_token, product):
        r = client.post("/api/v1/orders/",
                        json={"product_id": product["id"]},
                        headers=auth(user_token))
        assert r.status_code == 400
        assert "balans" in r.json()["detail"].lower()

    def test_cannot_buy_own_product(self, client, seller_token, product, db):
        from app import models
        seller = db.query(models.User).filter(models.User.username == "seller1").first()
        seller.balance = Decimal("100.00")
        db.commit()
        r = client.post("/api/v1/orders/",
                        json={"product_id": product["id"]},
                        headers=auth(seller_token))
        assert r.status_code == 400

    def test_balance_held_after_order(self, client, funded_buyer, product, db):
        from app import models
        client.post("/api/v1/orders/",
                    json={"product_id": product["id"]},
                    headers=auth(funded_buyer))
        buyer = db.query(models.User).filter(models.User.username == "buyer_rich").first()
        assert buyer.balance == Decimal("90.00")
        assert buyer.held_balance == Decimal("10.00")

    def test_create_order_no_auth(self, client, product):
        r = client.post("/api/v1/orders/", json={"product_id": product["id"]})
        assert r.status_code == 403


class TestOrderList:
    def test_list_as_buyer(self, client, funded_buyer, order):
        r = client.get("/api/v1/orders/?role=buyer", headers=auth(funded_buyer))
        assert r.status_code == 200
        assert r.json()["total"] == 1

    def test_list_as_seller(self, client, seller_token, order):
        r = client.get("/api/v1/orders/?role=seller", headers=auth(seller_token))
        assert r.status_code == 200
        assert r.json()["total"] == 1

    def test_filter_by_status(self, client, funded_buyer, order):
        r = client.get("/api/v1/orders/?role=buyer&status=PAID_HELD", headers=auth(funded_buyer))
        assert r.json()["total"] == 1
        r = client.get("/api/v1/orders/?role=buyer&status=COMPLETED", headers=auth(funded_buyer))
        assert r.json()["total"] == 0


class TestOrderGet:
    def test_get_order_as_buyer(self, client, funded_buyer, order):
        r = client.get(f"/api/v1/orders/{order['id']}", headers=auth(funded_buyer))
        assert r.status_code == 200

    def test_get_order_as_seller(self, client, seller_token, order):
        r = client.get(f"/api/v1/orders/{order['id']}", headers=auth(seller_token))
        assert r.status_code == 200

    def test_get_order_others_forbidden(self, client, order):
        other = register(client, "stranger")
        r = client.get(f"/api/v1/orders/{order['id']}", headers=auth(other))
        assert r.status_code == 403


class TestEscrowFlow:
    def test_seller_marks_delivered(self, client, seller_token, funded_buyer, order):
        oid = order["id"]
        r = client.post(f"/api/v1/orders/{oid}/deliver", headers=auth(seller_token))
        assert r.status_code == 200
        assert r.json()["status"] == "DELIVERED"

    def test_buyer_cant_mark_delivered(self, client, funded_buyer, order):
        r = client.post(f"/api/v1/orders/{order['id']}/deliver", headers=auth(funded_buyer))
        assert r.status_code == 403

    def test_buyer_completes_order(self, client, funded_buyer, seller_token, order):
        oid = order["id"]
        client.post(f"/api/v1/orders/{oid}/deliver", headers=auth(seller_token))
        r = client.post(f"/api/v1/orders/{oid}/complete", headers=auth(funded_buyer))
        assert r.status_code == 200
        assert r.json()["status"] == "COMPLETED"

    def test_seller_receives_funds_on_complete(self, client, funded_buyer, seller_token, order, db):
        from app import models
        oid = order["id"]
        client.post(f"/api/v1/orders/{oid}/deliver", headers=auth(seller_token))
        client.post(f"/api/v1/orders/{oid}/complete", headers=auth(funded_buyer))
        seller = db.query(models.User).filter(models.User.username == "seller1").first()
        assert seller.balance == Decimal("9.50")  # 10 - 5% komissiya

    def test_buyer_held_balance_released_on_complete(self, client, funded_buyer, seller_token, order, db):
        from app import models
        oid = order["id"]
        client.post(f"/api/v1/orders/{oid}/deliver", headers=auth(seller_token))
        client.post(f"/api/v1/orders/{oid}/complete", headers=auth(funded_buyer))
        buyer = db.query(models.User).filter(models.User.username == "buyer_rich").first()
        assert buyer.held_balance == Decimal("0.00")

    def test_seller_total_sales_increments(self, client, funded_buyer, seller_token, order, db):
        from app import models
        oid = order["id"]
        client.post(f"/api/v1/orders/{oid}/deliver", headers=auth(seller_token))
        client.post(f"/api/v1/orders/{oid}/complete", headers=auth(funded_buyer))
        seller = db.query(models.User).filter(models.User.username == "seller1").first()
        assert seller.total_sales == 1

    def test_full_escrow_flow_transaction_log(self, client, funded_buyer, seller_token, order, db):
        from app import models
        oid = order["id"]
        client.post(f"/api/v1/orders/{oid}/deliver", headers=auth(seller_token))
        client.post(f"/api/v1/orders/{oid}/complete", headers=auth(funded_buyer))
        txs = db.query(models.Transaction).all()
        types = {tx.type for tx in txs}
        assert "PAYMENT_HOLD" in types
        assert "PAYMENT_RELEASE" in types


class TestOrderCancel:
    def test_buyer_cancels_order(self, client, funded_buyer, order, db):
        from app import models
        r = client.post(f"/api/v1/orders/{order['id']}/cancel", headers=auth(funded_buyer))
        assert r.status_code == 200
        assert r.json()["status"] == "CANCELLED"
        buyer = db.query(models.User).filter(models.User.username == "buyer_rich").first()
        assert buyer.balance == Decimal("100.00")
        assert buyer.held_balance == Decimal("0.00")

    def test_seller_cancels_order(self, client, seller_token, funded_buyer, order):
        r = client.post(f"/api/v1/orders/{order['id']}/cancel", headers=auth(seller_token))
        assert r.status_code == 200
        assert r.json()["status"] == "CANCELLED"

    def test_cancel_completed_order_fails(self, client, funded_buyer, completed_order):
        r = client.post(f"/api/v1/orders/{completed_order['id']}/cancel", headers=auth(funded_buyer))
        assert r.status_code == 400

    def test_refund_transaction_created_on_cancel(self, client, funded_buyer, order, db):
        from app import models
        client.post(f"/api/v1/orders/{order['id']}/cancel", headers=auth(funded_buyer))
        refunds = db.query(models.Transaction).filter(models.Transaction.type == "REFUND").all()
        assert len(refunds) == 1


class TestOrderDispute:
    def test_open_dispute_as_buyer(self, client, funded_buyer, order):
        r = client.post(f"/api/v1/orders/{order['id']}/dispute",
                        json={"order_id": order["id"], "reason": "Tovar kelmadi"},
                        headers=auth(funded_buyer))
        assert r.status_code == 201
        assert r.json()["status"] == "OPEN"

    def test_order_status_becomes_dispute(self, client, funded_buyer, order, db):
        from app import models
        client.post(f"/api/v1/orders/{order['id']}/dispute",
                    json={"order_id": order["id"], "reason": "Sabab"},
                    headers=auth(funded_buyer))
        order_obj = db.query(models.Order).filter(
            models.Order.id == order["id"]
        ).first()
        assert order_obj.status == "DISPUTE"

    def test_duplicate_dispute_fails(self, client, funded_buyer, order):
        client.post(f"/api/v1/orders/{order['id']}/dispute",
                    json={"order_id": order["id"], "reason": "Sabab"},
                    headers=auth(funded_buyer))
        r = client.post(f"/api/v1/orders/{order['id']}/dispute",
                        json={"order_id": order["id"], "reason": "Yana"},
                        headers=auth(funded_buyer))
        assert r.status_code == 409

    def test_stranger_cannot_dispute(self, client, order):
        stranger = register(client, "stranger")
        r = client.post(f"/api/v1/orders/{order['id']}/dispute",
                        json={"order_id": order["id"], "reason": "Sabab"},
                        headers=auth(stranger))
        assert r.status_code == 403
