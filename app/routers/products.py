import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from typing import Optional
from uuid import UUID
from decimal import Decimal

from ..database import get_db
from ..models import Product, ProductImage, User
from ..schemas import ProductCreate, ProductOut, ProductCard, ProductImageOut, SuccessResponse
from ..utils.deps import get_current_user, require_seller
from ..utils.pagination import paginate, PagedResponse
from ..utils.logger import get_logger

router = APIRouter()
log = get_logger("products")


def _build_product_query(
    db: Session,
    game_id: Optional[UUID] = None,
    subcategory_id: Optional[UUID] = None,
    seller_id: Optional[UUID] = None,
    min_price: Optional[Decimal] = None,
    max_price: Optional[Decimal] = None,
    is_auto_delivery: Optional[bool] = None,
    has_discount: Optional[bool] = None,
    is_highlighted: Optional[bool] = None,
    search: Optional[str] = None,
    sort_by: str = "newest",
):
    q = db.query(Product).filter(Product.is_active == True)

    if game_id:
        q = q.filter(Product.game_id == game_id)
    if subcategory_id:
        q = q.filter(Product.subcategory_id == subcategory_id)
    if seller_id:
        q = q.filter(Product.seller_id == seller_id)
    if min_price is not None:
        q = q.filter(Product.price >= min_price)
    if max_price is not None:
        q = q.filter(Product.price <= max_price)
    if is_auto_delivery is not None:
        q = q.filter(Product.is_auto_delivery == is_auto_delivery)
    if has_discount is True:
        q = q.filter(Product.discount_percent != None)
    if is_highlighted is not None:
        q = q.filter(Product.is_highlighted == is_highlighted)
    if search:
        q = q.filter(Product.title.ilike(f"%{search}%"))

    if sort_by == "price_asc":
        q = q.order_by(Product.price.asc())
    elif sort_by == "price_desc":
        q = q.order_by(Product.price.desc())
    elif sort_by == "popular":
        q = q.order_by(Product.views.desc())
    elif sort_by == "reviews":
        q = q.order_by(Product.review_count.desc())
    else:
        q = q.order_by(Product.is_highlighted.desc(), Product.raised_at.desc())

    return q


@router.get("/", response_model=PagedResponse[ProductOut])
def list_products(
    game_id: Optional[UUID] = Query(None),
    subcategory_id: Optional[UUID] = Query(None),
    seller_id: Optional[UUID] = Query(None),
    min_price: Optional[Decimal] = Query(None, ge=0),
    max_price: Optional[Decimal] = Query(None, ge=0),
    is_auto_delivery: Optional[bool] = Query(None),
    has_discount: Optional[bool] = Query(None),
    is_highlighted: Optional[bool] = Query(None),
    search: Optional[str] = Query(None, max_length=200),
    sort_by: str = Query("newest", pattern="^(newest|price_asc|price_desc|popular|reviews)$"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    q = _build_product_query(
        db, game_id, subcategory_id, seller_id,
        min_price, max_price, is_auto_delivery,
        has_discount, is_highlighted, search, sort_by,
    )
    items, total, pages = paginate(q, page, size)
    return {"items": items, "total": total, "page": page, "size": size, "pages": pages}


@router.get("/my", response_model=PagedResponse[ProductOut])
def my_products(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    user: User = Depends(require_seller),
    db: Session = Depends(get_db),
):
    q = db.query(Product).filter(Product.seller_id == user.id).order_by(Product.raised_at.desc())
    items, total, pages = paginate(q, page, size)
    return {"items": items, "total": total, "page": page, "size": size, "pages": pages}


@router.get("/{product_id}", response_model=ProductOut)
def get_product(product_id: UUID, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product or not product.is_active:
        raise HTTPException(404, "Mahsulot topilmadi")
    product.views += 1
    db.commit()
    db.refresh(product)
    return product


@router.post("/", response_model=ProductOut, status_code=201)
def create_product(
    payload: ProductCreate,
    user: User = Depends(require_seller),
    db: Session = Depends(get_db),
):
    product = Product(seller_id=user.id, **payload.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    log.info(f"Yangi mahsulot: {product.id} | seller={user.username}")
    return product


@router.patch("/{product_id}", response_model=ProductOut)
def update_product(
    product_id: UUID,
    payload: ProductCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(404, "Mahsulot topilmadi")
    if product.seller_id != user.id and not user.is_admin:
        raise HTTPException(403, "Ruxsat yo'q")

    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(product, field, value)
    db.commit()
    db.refresh(product)
    return product


@router.delete("/{product_id}", response_model=SuccessResponse)
def delete_product(
    product_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(404, "Mahsulot topilmadi")
    if product.seller_id != user.id and not user.is_admin:
        raise HTTPException(403, "Ruxsat yo'q")

    product.is_active = False
    db.commit()
    log.info(f"Mahsulot o'chirildi: {product_id}")
    return {"message": "Mahsulot o'chirildi"}


@router.post("/{product_id}/bump", response_model=SuccessResponse)
def bump_product(
    product_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Ko'tarish — mahsulotni ro'yxat tepasiga chiqarish."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(404, "Mahsulot topilmadi")
    if product.seller_id != user.id:
        raise HTTPException(403, "Ruxsat yo'q")

    product.raised_at = datetime.datetime.utcnow()
    db.commit()
    log.info(f"Bump: {product_id}")
    return {"message": "Mahsulot ko'tarildi"}


@router.post("/{product_id}/images", response_model=ProductImageOut, status_code=201)
def add_product_image(
    product_id: UUID,
    image_url: str,
    sort_order: int = 0,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(404, "Mahsulot topilmadi")
    if product.seller_id != user.id and not user.is_admin:
        raise HTTPException(403, "Ruxsat yo'q")

    img = ProductImage(product_id=product_id, image_url=image_url, sort_order=sort_order)
    db.add(img)
    db.commit()
    db.refresh(img)
    return img


@router.delete("/{product_id}/images/{image_id}", response_model=SuccessResponse)
def delete_product_image(
    product_id: UUID,
    image_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(404, "Mahsulot topilmadi")
    if product.seller_id != user.id and not user.is_admin:
        raise HTTPException(403, "Ruxsat yo'q")

    img = db.query(ProductImage).filter(
        ProductImage.id == image_id,
        ProductImage.product_id == product_id,
    ).first()
    if not img:
        raise HTTPException(404, "Rasm topilmadi")

    db.delete(img)
    db.commit()
    return {"message": "Rasm o'chirildi"}
