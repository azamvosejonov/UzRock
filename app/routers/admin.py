import datetime
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional

from ..database import get_db
from ..models import (
    User, Product, Order, Dispute, WithdrawalRequest,
    Transaction, Category, Game, Subcategory, Notification,
)
from ..schemas import (
    UserOut, OrderOut, DisputeOut, WithdrawalOut, WithdrawalStatusUpdate,
    AdminStats, CategoryCreate, CategoryOut, GameCreate, GameOut,
    SubcategoryCreate, SubcategoryOut, SuccessResponse,
)
from ..utils.deps import require_admin
from ..utils.pagination import paginate, PagedResponse
from ..utils.logger import get_logger

router = APIRouter()
log = get_logger("admin")


# ── Dashboard ───────────────────────────────────────────────────

@router.get("/stats", response_model=AdminStats)
def get_stats(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    total_revenue_row = db.query(func.sum(Transaction.amount)).filter(
        Transaction.type == "PAYMENT_RELEASE"
    ).scalar() or Decimal("0")

    return {
        "total_users": db.query(User).count(),
        "total_sellers": db.query(User).filter(User.is_seller == True).count(),
        "total_products": db.query(Product).filter(Product.is_active == True).count(),
        "total_orders": db.query(Order).count(),
        "total_revenue": total_revenue_row,
        "open_disputes": db.query(Dispute).filter(Dispute.status == "OPEN").count(),
        "pending_withdrawals": db.query(WithdrawalRequest).filter(WithdrawalRequest.status == "PENDING").count(),
    }


# ── Users ───────────────────────────────────────────────────────

@router.get("/users", response_model=PagedResponse[UserOut])
def list_users(
    search: Optional[str] = Query(None),
    is_seller: Optional[bool] = Query(None),
    is_admin: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    q = db.query(User)
    if search:
        q = q.filter(
            User.username.ilike(f"%{search}%") | User.email.ilike(f"%{search}%")
        )
    if is_seller is not None:
        q = q.filter(User.is_seller == is_seller)
    if is_admin is not None:
        q = q.filter(User.is_admin == is_admin)
    q = q.order_by(User.created_at.desc())
    items, total, pages = paginate(q, page, size)
    return {"items": items, "total": total, "page": page, "size": size, "pages": pages}


@router.post("/users/{user_id}/make-admin", response_model=UserOut)
def make_admin(
    user_id: UUID,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "Foydalanuvchi topilmadi")
    user.is_admin = True
    db.commit()
    db.refresh(user)
    log.info(f"Admin berildi: {user.username}")
    return user


@router.post("/users/{user_id}/make-seller", response_model=UserOut)
def make_seller(
    user_id: UUID,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "Foydalanuvchi topilmadi")
    user.is_seller = True
    db.commit()
    db.refresh(user)
    return user


# ── Orders ──────────────────────────────────────────────────────

@router.get("/orders", response_model=PagedResponse[OrderOut])
def list_all_orders(
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    q = db.query(Order)
    if status:
        q = q.filter(Order.status == status.upper())
    q = q.order_by(Order.created_at.desc())
    items, total, pages = paginate(q, page, size)
    return {"items": items, "total": total, "page": page, "size": size, "pages": pages}


# ── Disputes ────────────────────────────────────────────────────

@router.get("/disputes", response_model=PagedResponse[DisputeOut])
def list_all_disputes(
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    q = db.query(Dispute)
    if status:
        q = q.filter(Dispute.status == status.upper())
    q = q.order_by(Dispute.created_at.desc())
    items, total, pages = paginate(q, page, size)
    return {"items": items, "total": total, "page": page, "size": size, "pages": pages}


# ── Withdrawals ─────────────────────────────────────────────────

@router.get("/withdrawals", response_model=PagedResponse[WithdrawalOut])
def list_withdrawals(
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    q = db.query(WithdrawalRequest)
    if status:
        q = q.filter(WithdrawalRequest.status == status.upper())
    q = q.order_by(WithdrawalRequest.created_at.desc())
    items, total, pages = paginate(q, page, size)
    return {"items": items, "total": total, "page": page, "size": size, "pages": pages}


@router.post("/withdrawals/{wr_id}/process", response_model=WithdrawalOut)
def process_withdrawal(
    wr_id: UUID,
    payload: WithdrawalStatusUpdate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    wr = db.query(WithdrawalRequest).filter(WithdrawalRequest.id == wr_id).first()
    if not wr:
        raise HTTPException(404, "So'rov topilmadi")
    if wr.status != "PENDING":
        raise HTTPException(400, "Bu so'rov allaqachon ko'rib chiqilgan")

    status = payload.status.upper()
    if status not in ("APPROVED", "REJECTED"):
        raise HTTPException(400, "Noto'g'ri status")

    wr.status = status
    wr.admin_note = payload.admin_note
    user = db.query(User).filter(User.id == wr.user_id).first()

    if status == "APPROVED":
        if user.balance < wr.amount:
            raise HTTPException(400, "Foydalanuvchi balansi yetarli emas")
        user.balance -= wr.amount
        tx = Transaction(
            user_id=user.id, type="WITHDRAW", amount=wr.amount,
            description=f"Pul chiqarish tasdiqlandi: {wr.address}",
        )
        db.add(tx)
        n = Notification(user_id=user.id, title="Pul chiqarish tasdiqlandi ✓", message=f"{wr.amount:,.0f} so'm chiqarildi")
    else:
        reason = payload.admin_note or "Ko'rsatilmagan"
        n = Notification(user_id=user.id, title="Pul chiqarish rad etildi", message=f"Sabab: {reason}")

    db.add(n)
    db.commit()
    db.refresh(wr)
    log.info(f"Withdrawal {status}: {wr_id} | admin={admin.username}")
    return wr


# ── Categories / Games / Subcategories (admin CRUD) ─────────────

@router.post("/categories", response_model=CategoryOut, status_code=201)
def create_category(payload: CategoryCreate, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    if db.query(Category).filter(Category.slug == payload.slug).first():
        raise HTTPException(409, "Bu slug mavjud")
    c = Category(**payload.model_dump())
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


@router.post("/games", response_model=GameOut, status_code=201)
def create_game(payload: GameCreate, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    if db.query(Game).filter(Game.slug == payload.slug).first():
        raise HTTPException(409, "Bu slug mavjud")
    g = Game(**payload.model_dump())
    db.add(g)
    db.commit()
    db.refresh(g)
    return g


@router.post("/subcategories", response_model=SubcategoryOut, status_code=201)
def create_subcategory(payload: SubcategoryCreate, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    s = Subcategory(**payload.model_dump())
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


# ── Product moderation ──────────────────────────────────────────

@router.post("/products/{product_id}/highlight", response_model=SuccessResponse)
def toggle_highlight(
    product_id: UUID,
    highlight: bool = True,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(404, "Mahsulot topilmadi")
    product.is_highlighted = highlight
    db.commit()
    status_word = "ta'kidlandi" if highlight else "oddiy holatga qaytdi"
    return {"message": f"Mahsulot {status_word}"}
