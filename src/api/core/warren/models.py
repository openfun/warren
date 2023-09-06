"""Warren's core models."""
from functools import reduce
from itertools import groupby
from typing import Any, Dict, List

import arrow
from pydantic.dataclasses import dataclass as pdt_dataclass
from pydantic.main import BaseModel
from ralph.backends.database.base import StatementParameters

from warren.fields import Date
from warren.filters import DatetimeRange

XAPI_STATEMENT = Dict[str, Any]


class DailyCount(BaseModel):
    """Base model to represent a count for a date."""

    date: Date
    count: int = 0

    def __add__(self, other):
        """Add counters for two DailyCount instances with the same date."""
        if self.date != other.date:
            raise Exception("Cannot add two DailyCount instances with different dates")
        return DailyCount(date=self.date, count=self.count + other.count)


class DailyCounts(BaseModel):
    """Base model to represent daily counts summary."""

    total: int = 0
    counts: List[DailyCount] = []

    @classmethod
    def from_range(cls, date_range: DatetimeRange):
        """Initialize DailyCounts from a date range."""
        return cls(
            counts=[
                DailyCount(date=d)
                for d in arrow.Arrow.range("day", date_range.since, date_range.until)
            ]
        )

    def merge_counts(self, counts: List[DailyCount]):
        """Merge DailyCount objects by date and aggregate counts.

        This method allows us to combine a list of DailyCount objects into
        the existing 'counts' list, aggregating the counts for each date
        and ensuring that 'counts' contains only unique DailyCount objects
        with one count per day.
        """
        self.counts += counts
        self.counts.sort(key=lambda x: x.date)
        self.counts = [
            reduce(lambda x, y: x + y, v)
            for k, v in groupby(self.counts, lambda dc: dc.date)
        ]
        self.total = sum(dc.count for dc in self.counts)


# FIXME: prefer using a valid generic pydantic model, this is too convoluted.
# See: https://github.com/openfun/ralph/issues/425
# Get a pydantic model from a stdlib dataclass to use Pydantic helpers
LRSStatementsQuery = pdt_dataclass(StatementParameters)
