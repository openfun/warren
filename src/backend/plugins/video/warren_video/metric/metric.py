"""Metric protocol and type definitions."""

from typing import Callable, List

from pydantic import BaseModel

# Represents a way to generate a metric from a list of statements.
from warren_video.lrs import XAPIStatement

from warren.filters import BaseQueryFilters

METRIC = Callable[[List[XAPIStatement], BaseQueryFilters], BaseModel]
