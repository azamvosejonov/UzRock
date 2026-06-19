import datetime
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional

from ..database import get_db
from ..models import Order, Product, User, Transaction, Notification, Dispute
from ..schemas import OrderCreate, OrderOut, DisputeCreate, DisputeOut, SuccessResponse
from ..utils.deps import get_current_user
from ..utils.pagination import paginate, PagedResponse
from ..utils.logger import get_logger

router = APIRouter()
log = get_logger("orders")

PLATFORM_COMMISSION = Decimal("0.05")  # 5%


def _notify(db: Session, user_id, title: str, message: str, link: str = None):
    n = Notification(user_id=user_id, title=title, message=message, link=link)
    db.add(n)


def _transaction(db: Session, user_id, order_id, t_type: str, amount: Decimal, desc: str):
    tx = Transaction(
        user_id=user_id,
        order_id=order_id,
        type=t_type,
        amount=amount,
        description=desc,
    )
    db.add(tx)


@router.post("/", response_model=OrderOut, status_code=201)
def create_order(
    payload: OrderCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    product = db.query(Product).filter(
        Product.id == payload.product_id,
        Product.is_active == True,
    ).first()
    if not product:
        raise HTTPException(404, "Mahsulot topilmadi")
    if product.seller_id == user.id:
        raise HTTPException(400, "O'z mahsulotingizni sotib ololmaysiz")

    amount = product.price
    if user.balance < amount:
        raise HTTPException(400, f"Balans yetarli emas. Kerak: {amount}, Mavjud: {user.balance}")

    # Escrow: balansdan ushlab qolish
    user.balance -= amount
    user.held_balance += amount

    order = Order(
        buyer_id=user.id,
        seller_id=product.seller_id,
        product_id=product.id,
        amount=amount,
        status="PAID_HELD",
    )
    db.add(order)
    db.flush()

    _transaction(db, user.id, order.id, "PAYMENT_HOLD", amount, f"Buyurtma #{order.id} uchun ushlab qolindi")
    _notify(db, product.seller_id, "Yangi buyurtma!", f"{user.username} sizdan mahsulot sotib oldi", f"/orders/{order.id}")

    db.commit()
    db.refresh(order)
    log.info(f"Buyurtma yaratildi: {order.id} | buyer={user.username} | amount={amount}")
    return order


@router.get("/", response_model=PagedResponse[OrderOut])
def list_my_orders(
    role: str = Query("buyer", pattern="^(buyer|seller)$"),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if role == "buyer":
        q = db.query(Order).filter(Order.buyer_id == user.id)
    else:
        q = db.query(Order).filter(Order.seller_id == user.id)

    if status:
        q = q.filter(Order.status == status.upper())

    q = q.order_by(Order.created_at.desc())
    items, total, pages = paginate(q, page, size)
    return {"items": items, "total": total, "page": page, "size": size, "pages": pages}


@router.get("/{order_id}", response_model=OrderOut)
def get_order(
    order_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(404, "Buyurtma topilmadi")
    if order.buyer_id != user.id and order.seller_id != user.id and not user.is_admin:
        raise HTTPException(403, "Ruxsat yo'q")
    return order


@router.post("/{order_id}/deliver", response_model=OrderOut)
def mark_delivered(
    order_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Sotuvchi tovarni yetkazdi deb belgilaydi."""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(404, "Buyurtma topilmadi")
    if order.seller_id != user.id:
        raise HTTPException(403, "Faqat sotuvchi belgilay oladi")
    if order.status != "PAID_HELD":
        raise HTTPException(400, f"Noto'g'ri holat: {order.status}")

    order.status = "DELIVERED"
    order.updated_at = datetime.datetime.utcnow()
    _notify(db, order.buyer_id, "Tovar yetkazildi!", "Tovarni qabul qiling yoki nizо oching", f"/orders/{order.id}")
    db.commit()
    db.refresh(order)
    log.info(f"Delivered: {order_id}")
    return order


@router.post("/{order_id}/complete", response_model=OrderOut)
def complete_order(
    order_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Xaridor tovarni qabul qildi — pul sotuvchiga o'tadi."""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(404, "Buyurtma topilmadi")
    if order.buyer_id != user.id:
        raise HTTPException(403, "Faqat xaridor tasdiqlaydi")
    if order.status not in ("DELIVERED", "PAID_HELD"):
        raise HTTPException(400, f"Noto'g'ri holat: {order.status}")

    seller = db.query(User).filter(User.id == order.seller_id).first()
    amount = order.amount
    commission = (amount * PLATFORM_COMMISSION).quantize(Decimal("0.01"))
    seller_receives = amount - commission

    # Escrow yechish
    user.held_balance -= amount
    seller.balance += seller_receives
    seller.total_sales += 1

    order.status = "COMPLETED"
    order.updated_at = datetime.datetime.utcnow()

    _transaction(db, order.seller_id, order.id, "PAYMENT_RELEASE", seller_receives,
                 f"Buyurtma #{order.id} uchun to'lov ({PLATFORM_COMMISSION*100:.0f}% komissiya)")
    _notify(db, order.seller_id, "To'lov qabul qilindi!", f"{seller_receives} so'm hisobingizga o'tdi", f"/orders/{order.id}")

    db.commit()
    db.refresh(order)
    log.info(f"Completed: {order_id} | seller_receives={seller_receives}")
    return order


@router.post("/{order_id}/cancel", response_model=OrderOut)
def cancel_order(
    order_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Buyurtmani bekor qilish — pul qaytariladi."""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(404, "Buyurtma topilmadi")
    if order.buyer_id != user.id and order.seller_id != user.id and not user.is_admin:
        raise HTTPException(403, "Ruxsat yo'q")
    if order.status in ("COMPLETED", "CANCELLED"):
        raise HTTPException(400, f"Bekor qilib bo'lmaydi: {order.status}")

    buyer = db.query(User).filter(User.id == order.buyer_id).first()

    if order.status == "PAID_HELD":
        buyer.held_balance -= order.amount
        buyer.balance += order.amount
        _transaction(db, order.buyer_id, order.id, "REFUND", order.amount, f"Buyurtma #{order.id} bekor qilindi, pul qaytarildi")

    order.status = "CANCELLED"
    order.updated_at = datetime.datetime.utcnow()

    notify_target = order.seller_id if user.id == order.buyer_id else order.buyer_id
    _notify(db, notify_target, "Buyurtma bekor qilindi", f"#{order.id} buyurtma bekor qilindi", f"/orders/{order.id}")

    db.commit()
    db.refresh(order)
    log.info(f"Cancelled: {order_id} | by={user.username}")
    return order


@router.post("/{order_id}/dispute", response_model=DisputeOut, status_code=201)
def open_dispute(
    order_id: UUID,
    payload: DisputeCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Nizо ochish (dispute)."""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(404, "Buyurtma topilmadi")
    if order.buyer_id != user.id and order.seller_id != user.id:
        raise HTTPException(403, "Ruxsat yo'q")
    if db.query(Dispute).filter(Dispute.order_id == order.id).first():
        raise HTTPException(409, "Bu buyurtma bo'yicha nizo allaqachon ochiq")
    if order.status not in ("PAID_HELD", "DELIVERED"):
        raise HTTPException(400, f"Nizo ochib bo'lmaydi: {order.status}")

    order.status = "DISPUTE"
    order.updated_at = datetime.datetime.utcnow()

    dispute = Dispute(order_id=order.id, reported_by=user.id, reason=payload.reason)
    db.add(dispute)

    other = order.seller_id if user.id == order.buyer_id else order.buyer_id
    _notify(db, other, "Nizo ochildi!", f"Buyurtma #{order.id} bo'yicha nizo ochildi", f"/orders/{order.id}")

    db.commit()
    db.refresh(dispute)
    log.info(f"Dispute: {dispute.id} | order={order_id} | by={user.username}")
    return dispute
