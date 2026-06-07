from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from enum import Enum


# ============================================================
#  ENUMS
# ============================================================
class OrderStatus(str, Enum):
    PENDING = "PENDING"
    PAID_HELD = "PAID_HELD"
    DELIVERED = "DELIVERED"
    COMPLETED = "COMPLETED"
    DISPUTE = "DISPUTE"
    CANCELLED = "CANCELLED"

class MessageType(str, Enum):
    TEXT = "TEXT"
    IMAGE = "IMAGE"
    SYSTEM = "SYSTEM"

class TransactionType(str, Enum):
    DEPOSIT = "DEPOSIT"
    WITHDRAW = "WITHDRAW"
    PAYMENT_HOLD = "PAYMENT_HOLD"
    PAYMENT_RELEASE = "PAYMENT_RELEASE"
    REFUND = "REFUND"


# ============================================================
#  1. USER SCHEMAS
# ============================================================
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: UUID
    username: str
    email: str
    avatar_url: Optional[str] = None
    balance: Decimal
    held_balance: Decimal
    is_seller: bool
    is_admin: bool
    is_on_vacation: bool
    total_sales: int
    response_time: int
    rating: float
    last_online: datetime
    created_at: datetime

    class Config:
        from_attributes = True

class UserPublicProfile(BaseModel):
    """What other users see (no email, no balance)."""
    id: UUID
    username: str
    avatar_url: Optional[str] = None
    is_seller: bool
    is_on_vacation: bool
    total_sales: int
    response_time: int
    rating: float
    last_online: datetime
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ============================================================
#  2. CATEGORY SCHEMAS
# ============================================================
class CategoryCreate(BaseModel):
    name: str
    slug: str

class CategoryOut(BaseModel):
    id: UUID
    name: str
    slug: str

    class Config:
        from_attributes = True


# ============================================================
#  3. GAME SCHEMAS
# ============================================================
class GameCreate(BaseModel):
    name: str
    slug: str
    category_id: UUID
    icon_url: Optional[str] = None
    is_new: bool = False

class GameOut(BaseModel):
    id: UUID
    name: str
    slug: str
    category_id: UUID
    icon_url: Optional[str] = None
    is_new: bool

    class Config:
        from_attributes = True


# ============================================================
#  4. SUBCATEGORY SCHEMAS
# ============================================================
class SubcategoryCreate(BaseModel):
    name: str
    slug: str
    game_id: UUID

class SubcategoryOut(BaseModel):
    id: UUID
    name: str
    slug: str
    game_id: UUID

    class Config:
        from_attributes = True


# ============================================================
#  5. PRODUCT IMAGE SCHEMAS
# ============================================================
class ProductImageOut(BaseModel):
    id: UUID
    image_url: str
    sort_order: int

    class Config:
        from_attributes = True


# ============================================================
#  6. PRODUCT SCHEMAS
# ============================================================
class ProductCreate(BaseModel):
    title: str = Field(..., max_length=300)
    description: Optional[str] = None
    price: Decimal = Field(..., gt=0)
    original_price: Optional[Decimal] = None
    discount_percent: Optional[int] = None
    delivery_method: Optional[str] = None
    delivery_details: Optional[str] = None
    is_auto_delivery: bool = False
    game_id: UUID
    subcategory_id: UUID
    dynamic_attributes: Optional[Dict[str, Any]] = None

class ProductOut(BaseModel):
    id: UUID
    seller_id: UUID
    game_id: UUID
    subcategory_id: UUID
    title: str
    description: Optional[str] = None
    price: Decimal
    original_price: Optional[Decimal] = None
    discount_percent: Optional[int] = None
    delivery_method: Optional[str] = None
    delivery_details: Optional[str] = None
    is_auto_delivery: bool
    dynamic_attributes: Optional[Dict[str, Any]] = None
    views: int
    review_count: int
    is_active: bool
    is_highlighted: bool
    images: List[ProductImageOut] = []
    created_at: datetime

    class Config:
        from_attributes = True

class ProductFilter(BaseModel):
    """Query params for filtering products."""
    game_id: Optional[UUID] = None
    subcategory_id: Optional[UUID] = None
    min_price: Optional[Decimal] = None
    max_price: Optional[Decimal] = None
    is_auto_delivery: Optional[bool] = None
    has_discount: Optional[bool] = None
    sort_by: Optional[str] = "newest"       # newest, price_asc, price_desc, popular


# ============================================================
#  7. ORDER SCHEMAS
# ============================================================
class OrderCreate(BaseModel):
    product_id: UUID

class OrderOut(BaseModel):
    id: UUID
    buyer_id: UUID
    seller_id: UUID
    product_id: UUID
    status: OrderStatus
    amount: Decimal
    payment_method: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class OrderStatusUpdate(BaseModel):
    status: OrderStatus


# ============================================================
#  8. MESSAGE SCHEMAS  (Chat)
# ============================================================
class MessageCreate(BaseModel):
    content: Optional[str] = None
    message_type: MessageType = MessageType.TEXT
    file_url: Optional[str] = None

class MessageOut(BaseModel):
    id: UUID
    order_id: UUID
    sender_id: UUID
    content: Optional[str] = None
    message_type: MessageType
    file_url: Optional[str] = None
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================
#  9. REVIEW SCHEMAS
# ============================================================
class ReviewCreate(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None

class ReviewReply(BaseModel):
    reply: str

class ReviewOut(BaseModel):
    id: UUID
    product_id: UUID
    buyer_id: UUID
    seller_id: UUID
    order_id: Optional[UUID] = None
    rating: int
    comment: Optional[str] = None
    reply: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================
#  10. TRANSACTION SCHEMAS
# ============================================================
class TransactionOut(BaseModel):
    id: UUID
    user_id: UUID
    order_id: Optional[UUID] = None
    type: TransactionType
    amount: Decimal
    description: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================
#  11. WITHDRAWAL SCHEMAS
# ============================================================
class WithdrawalCreate(BaseModel):
    amount: Decimal = Field(..., gt=0)
    address: str
    payment_method: Optional[str] = None

class WithdrawalOut(BaseModel):
    id: UUID
    user_id: UUID
    amount: Decimal
    address: str
    payment_method: Optional[str] = None
    status: str
    admin_note: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================
#  12. DISPUTE SCHEMAS
# ============================================================
class DisputeCreate(BaseModel):
    order_id: UUID
    reason: str

class DisputeOut(BaseModel):
    id: UUID
    order_id: UUID
    reported_by: UUID
    reason: str
    status: str
    admin_id: Optional[UUID] = None
    resolution_note: Optional[str] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================================
#  13. NOTIFICATION SCHEMAS
# ============================================================
class NotificationOut(BaseModel):
    id: UUID
    title: str
    message: str
    link: Optional[str] = None
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================
#  14. PAYMENT METHOD SCHEMAS
# ============================================================
class PaymentMethodOut(BaseModel):
    id: UUID
    name: str
    icon_url: Optional[str] = None
    is_active: bool

    class Config:
        from_attributes = True
