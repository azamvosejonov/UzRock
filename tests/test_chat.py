"""Chat — xabar yuborish va o'qish."""
from tests.conftest import register, auth


class TestMessages:
    def test_send_message_as_buyer(self, client, funded_buyer, order, seller_token):
        r = client.post(
            f"/api/v1/chat/{order['id']}/messages",
            json={"content": "Salom! Qachon yetkazasiz?", "message_type": "TEXT"},
            headers=auth(funded_buyer),
        )
        assert r.status_code == 201
        data = r.json()
        assert data["content"] == "Salom! Qachon yetkazasiz?"
        assert data["message_type"] == "TEXT"
        assert data["is_read"] is False

    def test_send_message_as_seller(self, client, seller_token, order):
        r = client.post(
            f"/api/v1/chat/{order['id']}/messages",
            json={"content": "10 daqiqada!", "message_type": "TEXT"},
            headers=auth(seller_token),
        )
        assert r.status_code == 201

    def test_get_messages(self, client, funded_buyer, seller_token, order):
        client.post(
            f"/api/v1/chat/{order['id']}/messages",
            json={"content": "Msg 1"},
            headers=auth(funded_buyer),
        )
        client.post(
            f"/api/v1/chat/{order['id']}/messages",
            json={"content": "Msg 2"},
            headers=auth(seller_token),
        )
        r = client.get(f"/api/v1/chat/{order['id']}/messages", headers=auth(funded_buyer))
        assert r.status_code == 200
        assert r.json()["total"] == 2

    def test_stranger_cannot_see_chat(self, client, order):
        stranger = register(client, "stranger")
        r = client.get(f"/api/v1/chat/{order['id']}/messages", headers=auth(stranger))
        assert r.status_code == 403

    def test_messages_marked_as_read_on_get(self, client, funded_buyer, seller_token, order, db):
        from app import models
        client.post(
            f"/api/v1/chat/{order['id']}/messages",
            json={"content": "Hello"},
            headers=auth(seller_token),
        )
        # Buyer reads messages — seller's message should be marked as read
        client.get(f"/api/v1/chat/{order['id']}/messages", headers=auth(funded_buyer))
        msgs = db.query(models.Message).filter(models.Message.order_id == order["id"]).all()
        assert all(m.is_read for m in msgs)

    def test_cannot_message_completed_order(self, client, funded_buyer, completed_order):
        r = client.post(
            f"/api/v1/chat/{completed_order['id']}/messages",
            json={"content": "Too late"},
            headers=auth(funded_buyer),
        )
        assert r.status_code == 400

    def test_send_image_message(self, client, funded_buyer, order):
        r = client.post(
            f"/api/v1/chat/{order['id']}/messages",
            json={"message_type": "IMAGE", "file_url": "https://cdn.test/proof.jpg"},
            headers=auth(funded_buyer),
        )
        assert r.status_code == 201
        assert r.json()["message_type"] == "IMAGE"
