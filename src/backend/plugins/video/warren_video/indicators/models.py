"""Defines the schema of what is returned inside the API responses."""
from typing import List

from pydantic.main import BaseModel

from warren.fields import Date


class VideoDayViews(BaseModel):
    """Model to represent video views for a date."""

    date: Date
    count: int = 0


class VideoViews(BaseModel):
    """Model to represent video views."""

    total_views: int = 0
    views_count_by_date: List[VideoDayViews] = []
