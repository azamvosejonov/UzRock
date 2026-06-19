from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List

from ..database import get_db
from ..models import Favorite, Product, User
from ..schemas import ProductOut, SuccessResponse
from ..utils.deps import get_current_user
from ..utils.pagination import paginate, PagedResponse

router = APIRouter()


@router.get("/", response_model=PagedResponse[ProductOut])
def my_favorites(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = (
        db.query(Product)
        .join(Favorite, Favorite.product_id == Product.id)
        .filter(Favorite.user_id == user.id, Product.is_active == True)
        .order_by(Favorite.created_at.desc())
    )
    items, total, pages = paginate(q, page, size)
    return {"items": items, "total": total, "page": page, "size": size, "pages": pages}


@router.post("/{product_id}", response_model=SuccessResponse, status_code=201)
def add_favorite(
    product_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    product = db.query(Product).filter(Product.id == product_id, Product.is_active == True).first()
    if not product:
        raise HTTPException(404, "Mahsulot topilmadi")
    exists = db.query(Favorite).filter(
        Favorite.user_id == user.id,
        Favorite.product_id == product_id,
    ).first()
    if exists:
        raise HTTPException(409, "Allaqachon sevimlilar ro'yxatida")

    db.add(Favorite(user_id=user.id, product_id=product_id))
    db.commit()
    return {"message": "Sevimlilarga qo'shildi"}


@router.delete("/{product_id}", response_model=SuccessResponse)
def remove_favorite(
    product_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    fav = db.query(Favorite).filter(
        Favorite.user_id == user.id,
        Favorite.product_id == product_id,
    ).first()
    if not fav:
        raise HTTPException(404, "Sevimlilar ro'yxatida yo'q")
    db.delete(fav)
    db.commit()
    return {"message": "Ro'yxatdan olib tashlandi"}
