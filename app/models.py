from sqlalchemy import (
    Column, String, Integer, Float, Text, ForeignKey,
    DateTime, DECIMAL, Boolean, Enum as SAEnum
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import datetime
import uuid
from .database import Base


# ============================================================
#  1. USER MODEL
# ============================================================
class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    avatar_url = Column(String(500), nullable=True)

    # --- Balance (Escrow) ---
    balance = Column(DECIMAL(12, 2), default=0.00)        # Available to withdraw
    held_balance = Column(DECIMAL(12, 2), default=0.00)    # Locked in Escrow

    # --- Roles ---
    is_seller = Column(Boolean, default=False)
    is_admin = Column(Boolean, default=False)

    # --- Seller Profile ---
    is_on_vacation = Column(Boolean, default=False)
    auto_reply = Column(String(500), nullable=True)
    response_time = Column(Integer, default=0)              # Avg response in minutes
    total_sales = Column(Integer, default=0)
    rating = Column(Float, default=0.0)

    last_online = Column(DateTime, default=datetime.datetime.utcnow)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # --- Relationships ---
    products = relationship("Product", back_populates="seller", lazy="dynamic")
    orders_as_buyer = relationship(
        "Order", foreign_keys="Order.buyer_id", back_populates="buyer"
    )
    orders_as_seller = relationship(
        "Order", foreign_keys="Order.seller_id", back_populates="seller"
    )
    reviews_written = relationship(
        "Review", foreign_keys="Review.buyer_id", back_populates="buyer"
    )
    reviews_received = relationship(
        "Review", foreign_keys="Review.seller_id", back_populates="seller"
    )
    notifications = relationship("Notification", back_populates="user")


# ============================================================
#  2. CATEGORY MODEL
# ============================================================
class Category(Base):
    __tablename__ = "categories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)              # "Игры", "Мобильные", "Приложения"
    slug = Column(String(100), unique=True, index=True, nullable=False)

    games = relationship("Game", back_populates="category", lazy="dynamic")


# ============================================================
#  3. GAME MODEL
# ============================================================
class Game(Base):
    __tablename__ = "games"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"), nullable=False)
    name = Column(String(200), nullable=False)
    slug = Column(String(200), unique=True, index=True, nullable=False)
    icon_url = Column(String(500), nullable=True)
    is_new = Column(Boolean, default=False)                 # "Новое" badge

    category = relationship("Category", back_populates="games")
    subcategories = relationship("Subcategory", back_populates="game")
    products = relationship("Product", back_populates="game", lazy="dynamic")


# ============================================================
#  4. SUBCATEGORY MODEL  (e.g. Робуксы, Аккаунты, Буст)
# ============================================================
class Subcategory(Base):
    __tablename__ = "subcategories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    game_id = Column(UUID(as_uuid=True), ForeignKey("games.id"), nullable=False)
    name = Column(String(100), nullable=False)
    slug = Column(String(100), index=True, nullable=False)

    game = relationship("Game", back_populates="subcategories")
    products = relationship("Product", back_populates="subcategory", lazy="dynamic")


# ============================================================
#  5. PRODUCT MODEL
# ============================================================
class Product(Base):
    __tablename__ = "products"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    seller_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    game_id = Column(UUID(as_uuid=True), ForeignKey("games.id"), nullable=False)
    subcategory_id = Column(UUID(as_uuid=True), ForeignKey("subcategories.id"), nullable=False)

    title = Column(String(300), nullable=False)
    description = Column(Text, nullable=True)

    # --- Pricing ---
    price = Column(DECIMAL(12, 2), nullable=False)
    original_price = Column(DECIMAL(12, 2), nullable=True)   # Crossed-out price
    discount_percent = Column(Integer, nullable=True)          # e.g. -16%

    # --- Delivery ---
    delivery_method = Column(String(200), nullable=True)       # "Автовыдача", "Вручную"
    delivery_details = Column(String(500), nullable=True)      # "Внутриигровой магазин"

    # --- Dynamic Attributes (JSONB) ---
    # { "platform": "PC", "region": "Global", "server": "EU" }
    dynamic_attributes = Column(JSONB, nullable=True)

    # --- Stats ---
    views = Column(Integer, default=0)
    review_count = Column(Integer, default=0)

    # --- Flags ---
    is_active = Column(Boolean, default=True)
    is_auto_delivery = Column(Boolean, default=False)          # Auto delivery badge
    is_highlighted = Column(Boolean, default=False)            # VIP/Premium listing

    raised_at = Column(DateTime, default=datetime.datetime.utcnow)  # Bump sort
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # --- Relationships ---
    seller = relationship("User", back_populates="products")
    game = relationship("Game", back_populates="products")
    subcategory = relationship("Subcategory", back_populates="products")
    images = relationship("ProductImage", back_populates="product", cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="product")


# ============================================================
#  6. PRODUCT IMAGE MODEL  (carousel/gallery)
# ============================================================
class ProductImage(Base):
    __tablename__ = "product_images"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    image_url = Column(String(500), nullable=False)
    sort_order = Column(Integer, default=0)

    product = relationship("Product", back_populates="images")


# ============================================================
#  7. ORDER MODEL  (Escrow/Garant)
# ============================================================
class Order(Base):
    __tablename__ = "orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    buyer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    seller_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)

    # Status Flow:
    # PENDING -> PAID_HELD -> DELIVERED -> COMPLETED
    #                      \-> DISPUTE -> RESOLVED
    #         \-> CANCELLED
    status = Column(
        SAEnum("PENDING", "PAID_HELD", "DELIVERED", "COMPLETED", "DISPUTE", "CANCELLED",
               name="order_status"),
        default="PENDING"
    )
    amount = Column(DECIMAL(12, 2), nullable=False)
    payment_method = Column(String(50), nullable=True)       # "Click", "Payme", "USDT"

    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # --- Relationships ---
    buyer = relationship("User", foreign_keys=[buyer_id], back_populates="orders_as_buyer")
    seller = relationship("User", foreign_keys=[seller_id], back_populates="orders_as_seller")
    messages = relationship("Message", back_populates="order", cascade="all, delete-orphan")
    dispute = relationship("Dispute", back_populates="order", uselist=False)


# ============================================================
#  8. MESSAGE MODEL  (Order Chat)
# ============================================================
class Message(Base):
    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    sender_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    content = Column(Text, nullable=True)
    message_type = Column(
        SAEnum("TEXT", "IMAGE", "SYSTEM", name="message_type"),
        default="TEXT"
    )
    file_url = Column(String(500), nullable=True)
    is_read = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    order = relationship("Order", back_populates="messages")
    sender = relationship("User")


# ============================================================
#  9. TRANSACTION MODEL  (Audit Log)
# ============================================================
class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=True)

    type = Column(
        SAEnum("DEPOSIT", "WITHDRAW", "PAYMENT_HOLD", "PAYMENT_RELEASE", "REFUND",
               name="transaction_type"),
        nullable=False
    )
    amount = Column(DECIMAL(12, 2), nullable=False)
    description = Column(String(500), nullable=True)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User")


# ============================================================
#  10. REVIEW MODEL
# ============================================================
class Review(Base):
    __tablename__ = "reviews"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    buyer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    seller_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=True)

    rating = Column(Integer, nullable=False)                  # 1-5
    comment = Column(Text, nullable=True)
    reply = Column(Text, nullable=True)                       # Seller reply

    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    product = relationship("Product", back_populates="reviews")
    buyer = relationship("User", foreign_keys=[buyer_id], back_populates="reviews_written")
    seller = relationship("User", foreign_keys=[seller_id], back_populates="reviews_received")


# ============================================================
#  11. FAVORITE MODEL
# ============================================================
class Favorite(Base):
    __tablename__ = "favorites"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), primary_key=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


# ============================================================
#  12. PAYMENT METHOD MODEL
# ============================================================
class PaymentMethod(Base):
    __tablename__ = "payment_methods"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)                # Click, Payme, USDT
    icon_url = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True)


# ============================================================
#  13. WITHDRAWAL REQUEST MODEL
# ============================================================
class WithdrawalRequest(Base):
    __tablename__ = "withdrawal_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    amount = Column(DECIMAL(12, 2), nullable=False)
    address = Column(String(200), nullable=False)             # Card number, Crypto wallet
    payment_method = Column(String(100), nullable=True)

    status = Column(
        SAEnum("PENDING", "APPROVED", "REJECTED", name="withdrawal_status"),
        default="PENDING"
    )
    admin_note = Column(String(500), nullable=True)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User")


# ============================================================
#  14. DISPUTE MODEL  (Arbitraj)
# ============================================================
class Dispute(Base):
    __tablename__ = "disputes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False)
    reported_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    reason = Column(Text, nullable=False)

    status = Column(
        SAEnum("OPEN", "RESOLVED_BUYER", "RESOLVED_SELLER", name="dispute_status"),
        default="OPEN"
    )
    admin_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    resolution_note = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)

    order = relationship("Order", back_populates="dispute")
    reporter = relationship("User", foreign_keys=[reported_by])
    admin = relationship("User", foreign_keys=[admin_id])


# ============================================================
#  15. NOTIFICATION MODEL
# ============================================================
class Notification(Base):
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title = Column(String(200), nullable=False)
    message = Column(String(500), nullable=False)
    link = Column(String(500), nullable=True)                  # deep-link to order/product
    is_read = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="notifications")
