from typing import TypeVar, Generic, List
from pydantic import BaseModel
from sqlalchemy.orm import Query

T = TypeVar("T")


class PagedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    size: int
    pages: int

    class Config:
        from_attributes = True


def paginate(query: Query, page: int, size: int):
    """Returns (items, total, pages)."""
    total = query.count()
    items = query.offset((page - 1) * size).limit(size).all()
    pages = max(1, (total + size - 1) // size)
    return items, total, pages
