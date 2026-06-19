from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from ..database import get_db
from ..models import Subcategory
from ..schemas import SubcategoryCreate, SubcategoryOut
from ..utils.deps import require_admin

router = APIRouter()


@router.get("/", response_model=List[SubcategoryOut])
def list_subcategories(
    game_id: UUID | None = Query(None),
    db: Session = Depends(get_db),
):
    q = db.query(Subcategory)
    if game_id:
        q = q.filter(Subcategory.game_id == game_id)
    return q.order_by(Subcategory.name).all()


@router.post("/", response_model=SubcategoryOut, status_code=201)
def create_subcategory(
    payload: SubcategoryCreate,
    db: Session = Depends(get_db),
    _: None = Depends(require_admin),
):
    sub = Subcategory(**payload.model_dump())
    db.add(sub)
    db.commit()
    db.refresh(sub)
    return sub


@router.delete("/{sub_id}", status_code=204)
def delete_subcategory(
    sub_id: UUID,
    db: Session = Depends(get_db),
    _: None = Depends(require_admin),
):
    sub = db.query(Subcategory).filter(Subcategory.id == sub_id).first()
    if not sub:
        raise HTTPException(404, "Subkategoriya topilmadi")
    db.delete(sub)
    db.commit()
