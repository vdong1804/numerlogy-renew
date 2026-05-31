"""Shared response wrappers."""

from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class DataResponse(BaseModel, Generic[T]):
    """Wraps payload in {"data": ...} matching Django DRF shape."""
    data: T
