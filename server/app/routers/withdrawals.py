from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import WithdrawalRequest, User, Notification
from ..schemas import WithdrawalCreate, WithdrawalOut
from ..utils.deps import get_current_user
from ..utils.pagination import paginate, PagedResponse
from ..utils.logger import get_logger

router = APIRouter()
log = get_logger("withdrawals")

MIN_WITHDRAWAL = 10_000  # 10,000 so'm


@router.post("/", response_model=WithdrawalOut, status_code=201)
def create_withdrawal(
    payload: WithdrawalCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not user.is_seller:
        raise HTTPException(403, "Faqat sotuvchilar pul chiqarishi mumkin")
    if payload.amount < MIN_WITHDRAWAL:
        raise HTTPException(400, f"Minimal summa: {MIN_WITHDRAWAL:,} so'm")
    if user.balance < payload.amount:
        raise HTTPException(400, f"Balans yetarli emas. Mavjud: {user.balance}")

    wr = WithdrawalRequest(
        user_id=user.id,
        amount=payload.amount,
        address=payload.address,
        payment_method=payload.payment_method,
    )
    db.add(wr)
    db.commit()
    db.refresh(wr)
    log.info(f"Withdrawal request: {wr.id} | user={user.username} | amount={payload.amount}")
    return wr


@router.get("/", response_model=PagedResponse[WithdrawalOut])
def my_withdrawals(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(WithdrawalRequest).filter(
        WithdrawalRequest.user_id == user.id
    ).order_by(WithdrawalRequest.created_at.desc())
    items, total, pages = paginate(q, page, size)
    return {"items": items, "total": total, "page": page, "size": size, "pages": pages}
