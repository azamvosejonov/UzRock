from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from ..database import get_db
from ..models import Game, Subcategory
from ..schemas import GameCreate, GameOut, SubcategoryOut
from ..utils.deps import require_admin

router = APIRouter()


@router.get("/", response_model=List[GameOut])
def list_games(
    category_id: UUID | None = Query(None),
    search: str | None = Query(None),
    db: Session = Depends(get_db),
):
    q = db.query(Game)
    if category_id:
        q = q.filter(Game.category_id == category_id)
    if search:
        q = q.filter(Game.name.ilike(f"%{search}%"))
    return q.order_by(Game.name).all()


@router.get("/{slug}", response_model=GameOut)
def get_game(slug: str, db: Session = Depends(get_db)):
    game = db.query(Game).filter(Game.slug == slug).first()
    if not game:
        raise HTTPException(404, "O'yin topilmadi")
    return game


@router.get("/{slug}/subcategories", response_model=List[SubcategoryOut])
def get_game_subcategories(slug: str, db: Session = Depends(get_db)):
    game = db.query(Game).filter(Game.slug == slug).first()
    if not game:
        raise HTTPException(404, "O'yin topilmadi")
    return db.query(Subcategory).filter(Subcategory.game_id == game.id).all()


@router.post("/", response_model=GameOut, status_code=201)
def create_game(
    payload: GameCreate,
    db: Session = Depends(get_db),
    _: None = Depends(require_admin),
):
    if db.query(Game).filter(Game.slug == payload.slug).first():
        raise HTTPException(409, "Bu slug allaqachon mavjud")
    game = Game(**payload.model_dump())
    db.add(game)
    db.commit()
    db.refresh(game)
    return game


@router.delete("/{slug}", status_code=204)
def delete_game(
    slug: str,
    db: Session = Depends(get_db),
    _: None = Depends(require_admin),
):
    game = db.query(Game).filter(Game.slug == slug).first()
    if not game:
        raise HTTPException(404, "O'yin topilmadi")
    db.delete(game)
    db.commit()
