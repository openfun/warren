"""Defines the schema of what is returned inside the API responses."""
from typing import List

from pydantic.main import BaseModel
from warren.fields import Date


class VideoDayViews(BaseModel):
    """Model to represent video views for a date."""

    date: Date
    count: int = 0


class DailyVideoViews(BaseModel):
    """Model to represent video views."""

    views_count_by_date: List[VideoDayViews] = []


class UniqueViewsCount(BaseModel):
    """Model to represent video views from distinct viewers."""
    total: int = 0
