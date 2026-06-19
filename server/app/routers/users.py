from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User, Product, Review
from ..schemas import UserPublicProfile, ProductOut, ReviewOut
from ..utils.pagination import paginate, PagedResponse

router = APIRouter()


@router.get("/{username}", response_model=UserPublicProfile)
def get_public_profile(username: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(404, "Foydalanuvchi topilmadi")
    return user


@router.get("/{username}/products", response_model=PagedResponse[ProductOut])
def get_seller_products(
    username: str,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(404, "Foydalanuvchi topilmadi")

    q = db.query(Product).filter(
        Product.seller_id == user.id,
        Product.is_active == True,
    ).order_by(Product.raised_at.desc())

    items, total, pages = paginate(q, page, size)
    return {"items": items, "total": total, "page": page, "size": size, "pages": pages}


@router.get("/{username}/reviews", response_model=PagedResponse[ReviewOut])
def get_seller_reviews(
    username: str,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(404, "Foydalanuvchi topilmadi")

    q = db.query(Review).filter(Review.seller_id == user.id).order_by(Review.created_at.desc())
    items, total, pages = paginate(q, page, size)
    return {"items": items, "total": total, "page": page, "size": size, "pages": pages}
