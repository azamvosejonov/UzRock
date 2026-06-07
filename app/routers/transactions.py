from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from ..database import get_db
from ..models import Transaction, User
from ..schemas import TransactionOut
from ..utils.deps import get_current_user
from ..utils.pagination import paginate, PagedResponse

router = APIRouter()


@router.get("/", response_model=PagedResponse[TransactionOut])
def my_transactions(
    tx_type: Optional[str] = Query(None, description="DEPOSIT|WITHDRAW|PAYMENT_HOLD|PAYMENT_RELEASE|REFUND"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(Transaction).filter(Transaction.user_id == user.id)
    if tx_type:
        q = q.filter(Transaction.type == tx_type.upper())
    q = q.order_by(Transaction.created_at.desc())
    items, total, pages = paginate(q, page, size)
    return {"items": items, "total": total, "page": page, "size": size, "pages": pages}
