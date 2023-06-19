"""TimeSeries metric for generating day time series from statements."""
from collections import Counter
from typing import Dict, List

import arrow
from pydantic import BaseModel

from warren.conf import settings
from warren.fields import Date
from warren.filters import BaseQueryFilters


class DayTimeSeriesDataPoint(BaseModel):
    """DayTimeSeries data point for a day."""

    day: Date
    total: int = 0

    class Config:
        """DayTimeSeriesDataPoint model configuration."""

        extra = "forbid"


class DayTimeSeries(BaseModel):
    """Time series using day intervals."""

    day_totals: List[DayTimeSeriesDataPoint]
    total: int

    def __init__(self, **data):
        """Instantiate a day time series from a list of DayTimeSeriesDataPoint."""
        data["total"] = 0

        super().__init__(**data)

        self.total = sum(day.total for day in self.day_totals)

    class Config:
        """DayTimeSeries model configuration."""

        extra = "forbid"


def create_day_time_series(
    statements: List[Dict], filters: BaseQueryFilters
) -> DayTimeSeries:
    """Generate a day time series from a list of statements and date filters.

    The day time series will have one value per day in the date range,
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
        DayTimeSeriesDataPoint(day=date, total=counter[date]) for date in date_range
    ]

    return DayTimeSeries(day_totals=daily_statements)
