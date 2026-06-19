from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..models import Category, Game
from ..schemas import CategoryCreate, CategoryOut, GameOut
from ..utils.deps import require_admin

router = APIRouter()


@router.get("/", response_model=List[CategoryOut])
def list_categories(db: Session = Depends(get_db)):
    return db.query(Category).order_by(Category.name).all()


@router.get("/{slug}", response_model=CategoryOut)
def get_category(slug: str, db: Session = Depends(get_db)):
    cat = db.query(Category).filter(Category.slug == slug).first()
    if not cat:
        raise HTTPException(404, "Kategoriya topilmadi")
    return cat


@router.get("/{slug}/games", response_model=List[GameOut])
def get_category_games(slug: str, db: Session = Depends(get_db)):
    cat = db.query(Category).filter(Category.slug == slug).first()
    if not cat:
        raise HTTPException(404, "Kategoriya topilmadi")
    return db.query(Game).filter(Game.category_id == cat.id).order_by(Game.name).all()


@router.post("/", response_model=CategoryOut, status_code=201)
def create_category(
    payload: CategoryCreate,
    db: Session = Depends(get_db),
    _: None = Depends(require_admin),
):
    if db.query(Category).filter(Category.slug == payload.slug).first():
        raise HTTPException(409, "Bu slug allaqachon mavjud")
    cat = Category(**payload.model_dump())
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat


@router.delete("/{slug}", status_code=204)
def delete_category(
    slug: str,
    db: Session = Depends(get_db),
    _: None = Depends(require_admin),
):
    cat = db.query(Category).filter(Category.slug == slug).first()
    if not cat:
        raise HTTPException(404, "Kategoriya topilmadi")
    db.delete(cat)
    db.commit()
