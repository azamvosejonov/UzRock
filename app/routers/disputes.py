import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional

from ..database import get_db
from ..models import Dispute, Order, User, Notification, Transaction
from ..schemas import DisputeOut, DisputeResolve
from ..utils.deps import get_current_user, require_admin
from ..utils.pagination import paginate, PagedResponse
from ..utils.logger import get_logger
from decimal import Decimal

router = APIRouter()
log = get_logger("disputes")


@router.get("/", response_model=PagedResponse[DisputeOut])
def list_disputes(
    status: Optional[str] = Query(None, description="OPEN|RESOLVED_BUYER|RESOLVED_SELLER"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    q = db.query(Dispute)
    if status:
        q = q.filter(Dispute.status == status.upper())
    q = q.order_by(Dispute.created_at.desc())
    items, total, pages = paginate(q, page, size)
    return {"items": items, "total": total, "page": page, "size": size, "pages": pages}


@router.get("/my", response_model=PagedResponse[DisputeOut])
def my_disputes(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(Dispute).filter(Dispute.reported_by == user.id).order_by(Dispute.created_at.desc())
    items, total, pages = paginate(q, page, size)
    return {"items": items, "total": total, "page": page, "size": size, "pages": pages}


@router.get("/{dispute_id}", response_model=DisputeOut)
def get_dispute(
    dispute_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    dispute = db.query(Dispute).filter(Dispute.id == dispute_id).first()
    if not dispute:
        raise HTTPException(404, "Nizo topilmadi")
    order = db.query(Order).filter(Order.id == dispute.order_id).first()
    if order.buyer_id != user.id and order.seller_id != user.id and not user.is_admin:
        raise HTTPException(403, "Ruxsat yo'q")
    return dispute


@router.post("/{dispute_id}/resolve", response_model=DisputeOut)
def resolve_dispute(
    dispute_id: UUID,
    payload: DisputeResolve,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Admin nizoni hal qiladi."""
    dispute = db.query(Dispute).filter(Dispute.id == dispute_id).first()
    if not dispute:
        raise HTTPException(404, "Nizo topilmadi")
    if dispute.status != "OPEN":
        raise HTTPException(400, "Nizo allaqachon hal qilingan")

    order = db.query(Order).filter(Order.id == dispute.order_id).first()
    buyer = db.query(User).filter(User.id == order.buyer_id).first()
    seller = db.query(User).filter(User.id == order.seller_id).first()
    amount = order.amount

    if payload.winner == "buyer":
        # Pul xaridorga qaytadi
        buyer.held_balance -= amount
        buyer.balance += amount
        tx = Transaction(
            user_id=buyer.id, order_id=order.id, type="REFUND",
            amount=amount, description=f"Nizo: admin xaridor foydasiga hal qildi",
        )
        db.add(tx)
        dispute.status = "RESOLVED_BUYER"
        _notify = (buyer.id, seller.id)
    else:
        # Pul sotuvchiga o'tadi (komissiysiz — admin qaror)
        buyer.held_balance -= amount
        seller.balance += amount
        seller.total_sales += 1
        tx = Transaction(
            user_id=seller.id, order_id=order.id, type="PAYMENT_RELEASE",
            amount=amount, description=f"Nizo: admin sotuvchi foydasiga hal qildi",
        )
        db.add(tx)
        dispute.status = "RESOLVED_SELLER"
        _notify = (seller.id, buyer.id)

    order.status = "COMPLETED"
    order.updated_at = datetime.datetime.utcnow()
    dispute.admin_id = admin.id
    dispute.resolution_note = payload.resolution_note
    dispute.resolved_at = datetime.datetime.utcnow()

    winner_id, loser_id = _notify
    n1 = Notification(user_id=winner_id, title="Nizo hal qilindi ✓", message=f"Siz foydasingizga hal qilindi: {payload.resolution_note[:100]}", link=f"/orders/{order.id}")
    n2 = Notification(user_id=loser_id, title="Nizo hal qilindi", message=f"Nizo boshqa tomon foydasiga hal qilindi: {payload.resolution_note[:100]}", link=f"/orders/{order.id}")
    db.add_all([n1, n2])

    db.commit()
    db.refresh(dispute)
    log.info(f"Dispute resolved: {dispute_id} | winner={payload.winner} | admin={admin.username}")
    return dispute
