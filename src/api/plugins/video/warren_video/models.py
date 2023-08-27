"""Defines the schema of what is returned inside the API responses."""
from typing import Union

from pydantic import BaseModel, validator

Seconds = Union[int, None]
Percent = Union[float, None]


class Info(BaseModel):
    """Base model to represent information for a video."""

    name: str | None
    length: Seconds
    completion_threshold: Percent

    @validator("length")
    @classmethod
    def length_must_be_positive(cls, v: Seconds) -> Seconds:
        """Validate video's length."""
        if v is not None and v < 0:
            raise ValueError("must be positive.")
        return v

    @validator("completion_threshold")
    @classmethod
    def completion_threshold_must_be_valid(cls, v: Percent) -> Percent:
        """Validate video's completion threshold."""
        if v is not None and (v < 0 or v > 1):
            raise ValueError("must be between 0 and 1.")
        return v
