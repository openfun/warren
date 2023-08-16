"""Warren's core models."""
from functools import reduce
from itertools import groupby
from typing import Any, Dict, List, Optional, Union

import arrow
from lti_toolbox.launch_params import LTIRole
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
        """Add counters for two DailyCount instances with the same date.

        Args:
            other (DailyCount): Another DailyCount instance with the same date.

        Returns:
            DailyCount: A new DailyCount instance with the combined count
            for the same date.

        Raises:
            ValueError: If 'other' has a different date than the current
            instance.

        Example:
            # Creating two DailyCount instances with the same date
            count1 = DailyCount(date="2023-09-19", count=10)
            count2 = DailyCount(date="2023-09-19", count=5)

            # Adding the counts for these instances
            total_count = count1 + count2

            # The 'total_count' instance now has a count of 15 for the same
            #  date "2023-09-19".

        Note:
            When adding two `DailyCount` instances, it's required that they
            have the same date. Attempting to add instances with different
            dates will raise a `ValueError`.

        """
        if self.date != other.date:
            raise ValueError("Cannot add two DailyCount instances with different dates")
        return DailyCount(date=self.date, count=self.count + other.count)


class DailyCounts(BaseModel):
    """Base model to represent daily counts summary."""

    total: int = 0
    counts: List[DailyCount] = []

    @classmethod
    def from_range(cls, date_range: DatetimeRange):
        """Initialize DailyCounts from a date range.

        Examples:
            # Initialize DailyCounts for a date range
            date_range = DatetimeRange(
                since=arrow.get("2023-01-01"),
                until=arrow.get("2023-01-05")
            )
            daily_counts = DailyCounts.from_range(date_range)
        """
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

        Examples:
            # Initialize DailyCounts for a date range
            date_range = DatetimeRange(
                since=arrow.get("2023-01-01"),
                until=arrow.get("2023-01-05")
            )
            daily_counts = DailyCounts.from_range(date_range)

            # Merge new DailyCount
            new_counts = [DailyCount(date="2023-09-19", count=10)]
            daily_counts.merge_counts(new_counts)

        Note:
            When merging `DailyCount` instances, the merged output will
            be sorted by ascending date.

        """
        self.counts += counts
        self.counts.sort(key=lambda x: x.date)
        self.counts = [
            reduce(lambda x, y: x + y, v)
            for k, v in groupby(self.counts, lambda dc: dc.date)
        ]
        # To remove for actors merging ? 
        self.total = sum(dc.count for dc in self.counts)


# FIXME: prefer using a valid generic pydantic model, this is too convoluted.
# See: https://github.com/openfun/ralph/issues/425
# Get a pydantic model from a stdlib dataclass to use Pydantic helpers
LRSStatementsQuery = pdt_dataclass(StatementParameters)


class LTIUser(BaseModel):
    """Model to represent LTI user data."""

    platform: str
    course: str
    email: str
    user: str


class LTIToken(BaseModel):
    """Model to represent JWT forged in an LTI context."""

    token_type: str
    exp: int
    iat: int
    jti: str
    session_id: str
    roles: List[Union[LTIRole, str]]
    user: LTIUser
    locale: str
    resource_link_id: str
    resource_link_description: Optional[str]
