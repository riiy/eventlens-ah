from pydantic import BaseModel
from typing import Generic, TypeVar

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    offset: int = 0
    limit: int = 20


class ErrorResponse(BaseModel):
    detail: str
    error_code: str | None = None