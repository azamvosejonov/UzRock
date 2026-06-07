from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional
from decimal import Decimal

from ..database import get_db
from ..models import Review, Order, Product, User, Notification
from ..schemas import ReviewCreate, ReviewReply, ReviewOut
from ..utils.deps import get_current_user
from ..utils.pagination import paginate, PagedResponse
from ..utils.logger import get_logger

router = APIRouter()
log = get_logger("reviews")


@router.get("/", response_model=PagedResponse[ReviewOut])
def list_reviews(
    seller_id: Optional[UUID] = Query(None),
    product_id: Optional[UUID] = Query(None),
    rating: Optional[int] = Query(None, ge=1, le=5),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    q = db.query(Review)
    if seller_id:
        q = q.filter(Review.seller_id == seller_id)
    if product_id:
        q = q.filter(Review.product_id == product_id)
    if rating:
        q = q.filter(Review.rating == rating)
    q = q.order_by(Review.created_at.desc())
    items, total, pages = paginate(q, page, size)
    return {"items": items, "total": total, "page": page, "size": size, "pages": pages}


@router.post("/", response_model=ReviewOut, status_code=201)
def create_review(
    payload: ReviewCreate,
    order_id: UUID = Query(..., description="Tugallangan buyurtma ID"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(404, "Buyurtma topilmadi")
    if order.buyer_id != user.id:
        raise HTTPException(403, "Faqat xaridor baho bera oladi")
    if order.status != "COMPLETED":
        raise HTTPException(400, "Faqat tugallangan buyurtmaga baho beriladi")
    if db.query(Review).filter(Review.order_id == order.id).first():
        raise HTTPException(409, "Bu buyurtmaga baho allaqachon berilgan")

    review = Review(
        product_id=order.product_id,
        buyer_id=user.id,
        seller_id=order.seller_id,
        order_id=order.id,
        rating=payload.rating,
        comment=payload.comment,
    )
    db.add(review)
    db.flush()

    # Mahsulot statistikasini yangilash
    product = db.query(Product).filter(Product.id == order.product_id).first()
    if product:
        product.review_count += 1

    # Sotuvchi reytingini qayta hisoblash
    seller = db.query(User).filter(User.id == order.seller_id).first()
    if seller:
        all_ratings = db.query(Review.rating).filter(Review.seller_id == seller.id).all()
        if all_ratings:
            seller.rating = round(sum(r[0] for r in all_ratings) / len(all_ratings), 2)

    n = Notification(
        user_id=order.seller_id,
        title="Yangi baho!",
        message=f"{user.username} {payload.rating}⭐ baho qoldirdi",
        link=f"/products/{order.product_id}",
    )
    db.add(n)
    db.commit()
    db.refresh(review)
    log.info(f"Review: {review.id} | seller={order.seller_id} | rating={payload.rating}")
    return review


@router.post("/{review_id}/reply", response_model=ReviewOut)
def reply_to_review(
    review_id: UUID,
    payload: ReviewReply,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Sotuvchi bahoga javob beradi."""
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(404, "Baho topilmadi")
    if review.seller_id != user.id:
        raise HTTPException(403, "Faqat sotuvchi javob bera oladi")
    if review.reply:
        raise HTTPException(400, "Javob allaqachon berilgan")

    review.reply = payload.reply
    n = Notification(
        user_id=review.buyer_id,
        title="Bahongizga javob!",
        message=f"Sotuvchi bahongizga javob berdi",
        link=f"/products/{review.product_id}",
    )
    db.add(n)
    db.commit()
    db.refresh(review)
    return review
