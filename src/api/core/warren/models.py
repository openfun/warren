"""Warren's core models."""
from enum import Enum
from typing import Any, Dict, Generic, TypeVar

from pydantic.main import BaseModel


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
