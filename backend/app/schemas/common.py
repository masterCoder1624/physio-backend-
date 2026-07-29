from typing import Generic, Optional, TypeVar, Any, List
from pydantic import BaseModel

T = TypeVar("T")


class PaginationMeta(BaseModel):
    page: int
    size: int
    total_items: int
    total_pages: int


class APIResponse(BaseModel, Generic[T]):
    success: bool = True
    message: str = "Operation completed successfully"
    data: Optional[T] = None
    errors: Optional[Any] = None
    meta: Optional[PaginationMeta] = None
