"""Defines the schema of what is returned inside the API responses."""
from typing import Union

from pydantic import BaseModel, validator


class Info(BaseModel):
    """Base model to represent information for a video."""

    name: str | None
    length: Union[PositiveInt, None]  # in Seconds
    completion_threshold: Union[confloat(gt=0.0, lt=1.0), None]  # in Percent
