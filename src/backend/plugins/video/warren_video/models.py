"""Defines the schema of what is returned inside the API responses."""
from typing import List, Dict

from pydantic.main import BaseModel
from warren.fields import Date


class VideoDayViews(BaseModel):
    """Model to represent video views for a date."""

    date: Date
    count: int = 0


class VideoViews(BaseModel):
    """Model to represent video views."""

    total_views: int = 0
    count_by_date: List[VideoDayViews] = []


class VideoEvents(BaseModel):
    """Represent the distribution of events (played, paused...) in a video."""
    events_per_second: Dict = None
