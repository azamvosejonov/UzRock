"""Bildirishnomalar — ro'yxat, o'qish."""
from app import models
from decimal import Decimal
from tests.conftest import register, auth


def _create_notification(db, user_id, title="Test", msg="Hello"):
    n = models.Notification(user_id=user_id, title=title, message=msg)
    db.add(n)
    db.commit()
    db.refresh(n)
    return n


class TestNotificationList:
    def test_list_empty(self, client, user_token):
        r = client.get("/api/v1/notifications/", headers=auth(user_token))
        assert r.status_code == 200
        assert r.json()["total"] == 0

    def test_list_with_notification(self, client, user_token, db):
        from app import models as m
        user = db.query(m.User).filter(m.User.username == "buyer1").first()
        _create_notification(db, user.id)
        r = client.get("/api/v1/notifications/", headers=auth(user_token))
        assert r.json()["total"] == 1

    def test_filter_unread_only(self, client, user_token, db):
        from app import models as m
        user = db.query(m.User).filter(m.User.username == "buyer1").first()
        n1 = _create_notification(db, user.id, "A", "A")
        n2 = _create_notification(db, user.id, "B", "B")
        n1.is_read = True
        db.commit()
        r = client.get("/api/v1/notifications/?unread_only=true", headers=auth(user_token))
        assert r.json()["total"] == 1

    def test_requires_auth(self, client):
        r = client.get("/api/v1/notifications/")
        assert r.status_code == 403


class TestUnreadCount:
    def test_unread_count(self, client, user_token, db):
        from app import models as m
        user = db.query(m.User).filter(m.User.username == "buyer1").first()
        _create_notification(db, user.id)
        _create_notification(db, user.id)
        r = client.get("/api/v1/notifications/unread-count", headers=auth(user_token))
        assert r.json()["count"] == 2

    def test_unread_count_zero_after_read(self, client, user_token, db):
        from app import models as m
        user = db.query(m.User).filter(m.User.username == "buyer1").first()
        _create_notification(db, user.id)
        client.post("/api/v1/notifications/read-all", headers=auth(user_token))
        r = client.get("/api/v1/notifications/unread-count", headers=auth(user_token))
        assert r.json()["count"] == 0


class TestMarkRead:
    def test_mark_one_read(self, client, user_token, db):
        from app import models as m
        user = db.query(m.User).filter(m.User.username == "buyer1").first()
        n = _create_notification(db, user.id)
        r = client.post(f"/api/v1/notifications/{n.id}/read", headers=auth(user_token))
        assert r.status_code == 200
        db.refresh(n)
        assert n.is_read is True

    def test_mark_all_read(self, client, user_token, db):
        from app import models as m
        user = db.query(m.User).filter(m.User.username == "buyer1").first()
        for _ in range(3):
            _create_notification(db, user.id)
        r = client.post("/api/v1/notifications/read-all", headers=auth(user_token))
        assert r.status_code == 200
        unread = db.query(m.Notification).filter(
            m.Notification.user_id == user.id,
            m.Notification.is_read == False,
        ).count()
        assert unread == 0


class TestOrderCreatesNotification:
    def test_order_notifies_seller(self, client, funded_buyer, product, seller_token, db):
        from app import models as m
        client.post("/api/v1/orders/", json={"product_id": product["id"]}, headers=auth(funded_buyer))
        seller = db.query(m.User).filter(m.User.username == "seller1").first()
        notifs = db.query(m.Notification).filter(m.Notification.user_id == seller.id).all()
        assert len(notifs) >= 1
