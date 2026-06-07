from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from uuid import UUID

from ..database import get_db
from ..models import Notification, User
from ..schemas import NotificationOut, SuccessResponse
from ..utils.deps import get_current_user
from ..utils.pagination import paginate, PagedResponse

router = APIRouter()


@router.get("/", response_model=PagedResponse[NotificationOut])
def my_notifications(
    unread_only: bool = Query(False),
    page: int = Query(1, ge=1),
    size: int = Query(30, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(Notification).filter(Notification.user_id == user.id)
    if unread_only:
        q = q.filter(Notification.is_read == False)
    q = q.order_by(Notification.created_at.desc())
    items, total, pages = paginate(q, page, size)
    return {"items": items, "total": total, "page": page, "size": size, "pages": pages}


@router.get("/unread-count")
def unread_count(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    count = db.query(Notification).filter(
        Notification.user_id == user.id,
        Notification.is_read == False,
    ).count()
    return {"count": count}


@router.post("/{notif_id}/read", response_model=SuccessResponse)
def mark_read(
    notif_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    n = db.query(Notification).filter(
        Notification.id == notif_id,
        Notification.user_id == user.id,
    ).first()
    if n:
        n.is_read = True
        db.commit()
    return {"message": "O'qildi"}


@router.post("/read-all", response_model=SuccessResponse)
def mark_all_read(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    db.query(Notification).filter(
        Notification.user_id == user.id,
        Notification.is_read == False,
    ).update({"is_read": True})
    db.commit()
    return {"message": "Barchasi o'qildi"}
