from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


# fmt: off
class Page(BaseModel, Generic[T]):
    """Страница результатов списочного запроса"""
    items:  list[T] = []
    total:  int     = 0
    limit:  int     = 50
    offset: int     = 0
# fmt: on
