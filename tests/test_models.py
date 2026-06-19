"""
15 ta model uchun unit testlar.
Har bir model: yaratish, maydonlar, default qiymatlar, bog'liqliklar.
"""
import uuid
from decimal import Decimal
from datetime import datetime

import pytest
from tests.conftest import register, auth, TestingSession
from app import models


# ── 1. User ──────────────────────────────────────────────────────

class TestUserModel:
    def test_create_user(self, db):
        u = models.User(
            username="alice",
            email="alice@test.uz",
            password_hash="hashed",
        )
        db.add(u)
        db.commit()
        db.refresh(u)
        assert u.id is not None
        assert u.username == "alice"
        assert u.balance == Decimal("0.00")
        assert u.held_balance == Decimal("0.00")
        assert u.is_seller is False
        assert u.is_admin is False
        assert u.is_on_vacation is False
        assert u.total_sales == 0
        assert u.rating == 0.0

    def test_user_unique_email(self, db):
        db.add(models.User(username="a", email="dup@test.uz", password_hash="h"))
        db.commit()
        db.add(models.User(username="b", email="dup@test.uz", password_hash="h"))
        with pytest.raises(Exception):
            db.commit()

    def test_user_balance_operations(self, db):
        u = models.User(username="rich", email="rich@test.uz", password_hash="h")
        db.add(u)
        db.commit()
        u.balance = Decimal("500.00")
        u.held_balance = Decimal("50.00")
        db.commit()
        db.refresh(u)
        assert u.balance == Decimal("500.00")
        assert u.held_balance == Decimal("50.00")


# ── 2. Category ──────────────────────────────────────────────────

class TestCategoryModel:
    def test_create_category(self, db):
        c = models.Category(name="O'yinlar", slug="games")
        db.add(c)
        db.commit()
        db.refresh(c)
        assert c.id is not None
        assert c.slug == "games"

    def test_category_unique_slug(self, db):
        db.add(models.Category(name="A", slug="same"))
        db.commit()
        db.add(models.Category(name="B", slug="same"))
        with pytest.raises(Exception):
            db.commit()


# ── 3. Game ──────────────────────────────────────────────────────

class TestGameModel:
    def test_create_game(self, db):
        cat = models.Category(name="Games", slug="games")
        db.add(cat)
        db.commit()
        game = models.Game(
            category_id=cat.id,
            name="Roblox",
            slug="roblox",
        )
        db.add(game)
        db.commit()
        db.refresh(game)
        assert game.id is not None
        assert game.is_new is False
        assert str(game.category_id) == str(cat.id)

    def test_game_is_new_flag(self, db):
        cat = models.Category(name="G", slug="g")
        db.add(cat)
        db.commit()
        game = models.Game(category_id=cat.id, name="New Game", slug="new-game", is_new=True)
        db.add(game)
        db.commit()
        db.refresh(game)
        assert game.is_new is True


# ── 4. Subcategory ───────────────────────────────────────────────

class TestSubcategoryModel:
    def test_create_subcategory(self, db):
        cat = models.Category(name="G", slug="g")
        db.add(cat)
        db.commit()
        game = models.Game(category_id=cat.id, name="Roblox", slug="roblox")
        db.add(game)
        db.commit()
        sub = models.Subcategory(game_id=game.id, name="Robux", slug="robux")
        db.add(sub)
        db.commit()
        db.refresh(sub)
        assert sub.id is not None
        assert sub.name == "Robux"


# ── 5. Product ───────────────────────────────────────────────────

class TestProductModel:
    def _make_base(self, db):
        u = models.User(username="seller", email="s@test.uz", password_hash="h", is_seller=True)
        cat = models.Category(name="G", slug="g")
        db.add_all([u, cat])
        db.commit()
        game = models.Game(category_id=cat.id, name="Roblox", slug="roblox")
        db.add(game)
        db.commit()
        sub = models.Subcategory(game_id=game.id, name="Robux", slug="robux")
        db.add(sub)
        db.commit()
        return u, game, sub

    def test_create_product(self, db):
        u, game, sub = self._make_base(db)
        p = models.Product(
            seller_id=u.id,
            game_id=game.id,
            subcategory_id=sub.id,
            title="100 Robux",
            price=Decimal("10.00"),
        )
        db.add(p)
        db.commit()
        db.refresh(p)
        assert p.id is not None
        assert p.is_active is True
        assert p.views == 0
        assert p.review_count == 0
        assert p.is_highlighted is False

    def test_product_with_jsonb(self, db):
        u, game, sub = self._make_base(db)
        p = models.Product(
            seller_id=u.id, game_id=game.id, subcategory_id=sub.id,
            title="Test", price=Decimal("5.00"),
            dynamic_attributes={"platform": "PC", "region": "Global"},
        )
        db.add(p)
        db.commit()
        db.refresh(p)
        assert p.dynamic_attributes["platform"] == "PC"

    def test_product_discount(self, db):
        u, game, sub = self._make_base(db)
        p = models.Product(
            seller_id=u.id, game_id=game.id, subcategory_id=sub.id,
            title="Sale", price=Decimal("8.00"),
            original_price=Decimal("10.00"),
            discount_percent=20,
        )
        db.add(p)
        db.commit()
        db.refresh(p)
        assert p.discount_percent == 20
        assert p.original_price == Decimal("10.00")


# ── 6. ProductImage ──────────────────────────────────────────────

class TestProductImageModel:
    def test_create_image(self, db):
        u = models.User(username="s", email="s@test.uz", password_hash="h")
        cat = models.Category(name="G", slug="g")
        db.add_all([u, cat])
        db.commit()
        game = models.Game(category_id=cat.id, name="G", slug="g")
        db.add(game)
        db.commit()
        sub = models.Subcategory(game_id=game.id, name="S", slug="s")
        db.add(sub)
        db.commit()
        p = models.Product(seller_id=u.id, game_id=game.id, subcategory_id=sub.id,
                           title="P", price=Decimal("1.00"))
        db.add(p)
        db.commit()
        img = models.ProductImage(product_id=p.id, image_url="https://img.test/1.jpg", sort_order=0)
        db.add(img)
        db.commit()
        db.refresh(img)
        assert img.id is not None
        assert img.sort_order == 0


# ── 7. Order ─────────────────────────────────────────────────────

class TestOrderModel:
    def test_order_status_default(self, db):
        buyer = models.User(username="b", email="b@test.uz", password_hash="h")
        seller = models.User(username="s", email="s@test.uz", password_hash="h")
        cat = models.Category(name="G", slug="g")
        db.add_all([buyer, seller, cat])
        db.commit()
        game = models.Game(category_id=cat.id, name="G", slug="g")
        db.add(game)
        db.commit()
        sub = models.Subcategory(game_id=game.id, name="S", slug="s")
        db.add(sub)
        db.commit()
        product = models.Product(seller_id=seller.id, game_id=game.id,
                                 subcategory_id=sub.id, title="P", price=Decimal("10.00"))
        db.add(product)
        db.commit()
        order = models.Order(
            buyer_id=buyer.id, seller_id=seller.id,
            product_id=product.id, amount=Decimal("10.00"),
            status="PENDING",
        )
        db.add(order)
        db.commit()
        db.refresh(order)
        assert order.status == "PENDING"
        assert order.amount == Decimal("10.00")

    def test_order_status_transitions(self, db):
        buyer = models.User(username="b", email="b@test.uz", password_hash="h")
        seller = models.User(username="s", email="s@test.uz", password_hash="h")
        cat = models.Category(name="G", slug="g")
        db.add_all([buyer, seller, cat])
        db.commit()
        game = models.Game(category_id=cat.id, name="G", slug="g")
        db.add(game)
        db.commit()
        sub = models.Subcategory(game_id=game.id, name="S", slug="s")
        db.add(sub)
        db.commit()
        product = models.Product(seller_id=seller.id, game_id=game.id,
                                 subcategory_id=sub.id, title="P", price=Decimal("5.00"))
        db.add(product)
        db.commit()
        order = models.Order(buyer_id=buyer.id, seller_id=seller.id,
                             product_id=product.id, amount=Decimal("5.00"), status="PENDING")
        db.add(order)
        db.commit()
        for status in ("PAID_HELD", "DELIVERED", "COMPLETED"):
            order.status = status
            db.commit()
            db.refresh(order)
            assert order.status == status


# ── 8. Message ───────────────────────────────────────────────────

class TestMessageModel:
    def test_message_defaults(self, db):
        sender = models.User(username="u", email="u@test.uz", password_hash="h")
        buyer = models.User(username="b", email="b@test.uz", password_hash="h")
        seller = models.User(username="s", email="s@test.uz", password_hash="h")
        cat = models.Category(name="G", slug="g")
        db.add_all([sender, buyer, seller, cat])
        db.commit()
        game = models.Game(category_id=cat.id, name="G", slug="g")
        db.add(game)
        db.commit()
        sub = models.Subcategory(game_id=game.id, name="S", slug="s")
        db.add(sub)
        db.commit()
        product = models.Product(seller_id=seller.id, game_id=game.id,
                                 subcategory_id=sub.id, title="P", price=Decimal("1.00"))
        db.add(product)
        db.commit()
        order = models.Order(buyer_id=buyer.id, seller_id=seller.id,
                             product_id=product.id, amount=Decimal("1.00"), status="PAID_HELD")
        db.add(order)
        db.commit()
        msg = models.Message(order_id=order.id, sender_id=sender.id, content="Salom!")
        db.add(msg)
        db.commit()
        db.refresh(msg)
        assert msg.message_type == "TEXT"
        assert msg.is_read is False


# ── 9. Transaction ───────────────────────────────────────────────

class TestTransactionModel:
    def test_transaction_types(self, db):
        u = models.User(username="u", email="u@test.uz", password_hash="h")
        db.add(u)
        db.commit()
        for tx_type in ("DEPOSIT", "WITHDRAW", "PAYMENT_HOLD", "PAYMENT_RELEASE", "REFUND"):
            tx = models.Transaction(user_id=u.id, type=tx_type, amount=Decimal("10.00"))
            db.add(tx)
        db.commit()
        txs = db.query(models.Transaction).filter(models.Transaction.user_id == u.id).all()
        assert len(txs) == 5


# ── 10. Review ───────────────────────────────────────────────────

class TestReviewModel:
    def test_review_rating_range(self, db):
        buyer = models.User(username="b", email="b@test.uz", password_hash="h")
        seller = models.User(username="s", email="s@test.uz", password_hash="h")
        cat = models.Category(name="G", slug="g")
        db.add_all([buyer, seller, cat])
        db.commit()
        game = models.Game(category_id=cat.id, name="G", slug="g")
        db.add(game)
        db.commit()
        sub = models.Subcategory(game_id=game.id, name="S", slug="s")
        db.add(sub)
        db.commit()
        product = models.Product(seller_id=seller.id, game_id=game.id,
                                 subcategory_id=sub.id, title="P", price=Decimal("1.00"))
        db.add(product)
        db.commit()
        review = models.Review(
            product_id=product.id, buyer_id=buyer.id,
            seller_id=seller.id, rating=5, comment="Zo'r!",
        )
        db.add(review)
        db.commit()
        db.refresh(review)
        assert review.rating == 5
        assert review.reply is None


# ── 11. Favorite ─────────────────────────────────────────────────

class TestFavoriteModel:
    def test_favorite_composite_pk(self, db):
        u = models.User(username="u", email="u@test.uz", password_hash="h")
        seller = models.User(username="s", email="s@test.uz", password_hash="h")
        cat = models.Category(name="G", slug="g")
        db.add_all([u, seller, cat])
        db.commit()
        game = models.Game(category_id=cat.id, name="G", slug="g")
        db.add(game)
        db.commit()
        sub = models.Subcategory(game_id=game.id, name="S", slug="s")
        db.add(sub)
        db.commit()
        p = models.Product(seller_id=seller.id, game_id=game.id,
                           subcategory_id=sub.id, title="P", price=Decimal("1.00"))
        db.add(p)
        db.commit()
        fav = models.Favorite(user_id=u.id, product_id=p.id)
        db.add(fav)
        db.commit()
        count = db.query(models.Favorite).filter(models.Favorite.user_id == u.id).count()
        assert count == 1


# ── 12. PaymentMethod ────────────────────────────────────────────

class TestPaymentMethodModel:
    def test_create_payment_method(self, db):
        pm = models.PaymentMethod(name="Click", is_active=True)
        db.add(pm)
        db.commit()
        db.refresh(pm)
        assert pm.id is not None
        assert pm.is_active is True


# ── 13. WithdrawalRequest ────────────────────────────────────────

class TestWithdrawalModel:
    def test_withdrawal_default_pending(self, db):
        u = models.User(username="u", email="u@test.uz", password_hash="h")
        db.add(u)
        db.commit()
        wr = models.WithdrawalRequest(
            user_id=u.id, amount=Decimal("50.00"),
            address="9860123456789012", payment_method="Click",
        )
        db.add(wr)
        db.commit()
        db.refresh(wr)
        assert wr.status == "PENDING"
        assert wr.admin_note is None


# ── 14. Dispute ──────────────────────────────────────────────────

class TestDisputeModel:
    def test_dispute_default_open(self, db):
        buyer = models.User(username="b", email="b@test.uz", password_hash="h")
        seller = models.User(username="s", email="s@test.uz", password_hash="h")
        cat = models.Category(name="G", slug="g")
        db.add_all([buyer, seller, cat])
        db.commit()
        game = models.Game(category_id=cat.id, name="G", slug="g")
        db.add(game)
        db.commit()
        sub = models.Subcategory(game_id=game.id, name="S", slug="s")
        db.add(sub)
        db.commit()
        product = models.Product(seller_id=seller.id, game_id=game.id,
                                 subcategory_id=sub.id, title="P", price=Decimal("1.00"))
        db.add(product)
        db.commit()
        order = models.Order(buyer_id=buyer.id, seller_id=seller.id,
                             product_id=product.id, amount=Decimal("1.00"), status="DISPUTE")
        db.add(order)
        db.commit()
        dispute = models.Dispute(order_id=order.id, reported_by=buyer.id, reason="Yetmadi")
        db.add(dispute)
        db.commit()
        db.refresh(dispute)
        assert dispute.status == "OPEN"
        assert dispute.resolved_at is None


# ── 15. Notification ─────────────────────────────────────────────

class TestNotificationModel:
    def test_notification_unread_by_default(self, db):
        u = models.User(username="u", email="u@test.uz", password_hash="h")
        db.add(u)
        db.commit()
        n = models.Notification(user_id=u.id, title="Test", message="Hello")
        db.add(n)
        db.commit()
        db.refresh(n)
        assert n.is_read is False
        assert n.link is None
