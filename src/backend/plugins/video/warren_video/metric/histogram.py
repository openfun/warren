"""Histogram metric for generating simple histograms from statements."""
from collections import Counter
from typing import Dict, List

import arrow
from pydantic import BaseModel

from warren.conf import settings
from warren.fields import Date
from warren.filters import BaseQueryFilters


class HistogramDay(BaseModel):
    """Histogram value for a day."""

    day: Date
    total: int = 0


class Histogram(BaseModel):
    """Histogram over a day range."""

    day_totals: List[HistogramDay]
    total: int

    def __init__(self, **data):
        """Instantiate a histogram from a list of day totals."""
        data["total"] = 0

        super().__init__(**data)

        self.total = sum(day.total for day in self.day_totals)


def histogram_metric(statements: List[Dict], filters: BaseQueryFilters) -> Histogram:
    """Generate an histogram from a list of statements and date filters.

    The histogram will have one value per day in the date range,
    even when 0 statements were found for the given day.
    """
    date_range = [
        d.format(settings.DATE_FORMAT)
        for d in arrow.Arrow.range("day", filters.since, filters.until)
    ]

    timestamps = [
        arrow.get(statement["timestamp"]).format(settings.DATE_FORMAT)
        for statement in statements
    ]

    counter = Counter(timestamps)

    daily_statements = [
        HistogramDay(day=date, total=counter[date]) for date in date_range
    ]

    return Histogram(day_totals=daily_statements)
