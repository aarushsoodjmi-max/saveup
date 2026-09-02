from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class PaginationMeta(BaseModel):
    page: int
    limit: int
    total: int
    total_pages: int


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    meta: PaginationMeta


def build_pagination_meta(*, page: int, limit: int, total: int) -> PaginationMeta:
    total_pages = (total + limit - 1) // limit if limit else 0
    return PaginationMeta(page=page, limit=limit, total=total, total_pages=max(total_pages, 0))


class MessageResponse(BaseModel):
    message: str
