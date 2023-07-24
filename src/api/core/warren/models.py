"""Warren's core models."""
from enum import Enum
from typing import Any, Dict, Generic, List, TypeVar

from pydantic.main import BaseModel

from warren.fields import Date


class StatusEnum(str, Enum):
    """Enum for status types."""

    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class Error(BaseModel):
    """Basic error model."""

    error_message: str


T = TypeVar("T")


class Response(BaseModel, Generic[T]):
    """Generic response model."""

    status: StatusEnum
    content: T


XAPI_STATEMENT = Dict[str, Any]


class DailyCount(BaseModel):
    """Base model to represent a count for a date."""

    date: Date
    count: int = 0


class DailyCounts(BaseModel):
    """Base model to represent daily counts summary."""

    total_count: int = 0
    count_by_date: List[DailyCount] = []
