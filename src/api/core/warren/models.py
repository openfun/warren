"""Warren's core models."""

from datetime import datetime
from functools import reduce
from itertools import groupby
from typing import Any, Dict, List, Optional, Set

import arrow
from lti_toolbox.launch_params import LTIRole
from pydantic.main import BaseModel

from warren.fields import Date

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


class DailyUniqueCount(BaseModel):
    """Base model to represent a unique user count for a date."""

    date: Date
    count: int = 0
    users: Set[str] = set()

    def __add__(self, other):
        """Add counters for two DailyUniqueCount instances with the same date.

        Args:
            other (DailyUniqueCount): Another DailyUniqueCount instance with the
            same date.

        Returns:
            DailyUniqueCount: A new DailyUniqueCount instance with the combined count
            for the same date.

        Raises:
            ValueError: If 'other' has a different date than the current
            instance.

        Example:
            # Creating two DailyUniqueCount instances with the same date
            count1 = DailyUniqueCount(date="2023-09-19", count=10)
            count2 = DailyUniqueCount(date="2023-09-19", count=5)

            # Adding the counts for these instances
            total_count = count1 + count2

            # The 'total_count' instance now has a count of 15 for the same
            #  date "2023-09-19".

        Note:
            When adding two `DailyUniqueCount` instances, it's required that they
            have the same date. Attempting to add instances with different
            dates will raise a `ValueError`.

        """
        if self.date != other.date:
            raise ValueError(
                "Cannot add two DailyUniqueCount instances with different dates"
            )
        users = self.users | other.users
        return DailyUniqueCount(date=self.date, count=len(users), users=users)

    def to_daily_count(self):
        """Convert DailyUniqueCount to DailyCount."""
        return DailyCount(date=self.date, count=self.count)


class DailyCounts(BaseModel):
    """Base model to represent daily counts summary."""

    total: int = 0
    counts: List[DailyCount] = []

    @classmethod
    def from_range(cls, since: datetime, until: datetime):
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
            counts=[DailyCount(date=d) for d in arrow.Arrow.range("day", since, until)]
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
        self.total = sum(dc.count for dc in self.counts)


class DailyUniqueCounts(BaseModel):
    """Base model to represent daily unique counts summary."""

    total: int = 0
    counts: List[DailyUniqueCount] = []

    @classmethod
    def from_range(cls, since: datetime, until: datetime):
        """Initialize DailyUniqueCounts from a date range.

        Examples:
            # Initialize DailyUniqueCounts for a date range
            date_range = DatetimeRange(
                since=arrow.get("2023-01-01"),
                until=arrow.get("2023-01-05")
            )
            daily_unique_counts = DailyUniqueCounts.from_range(date_range)
        """
        return cls(
            counts=[
                DailyUniqueCount(date=d) for d in arrow.Arrow.range("day", since, until)
            ]
        )

    def merge_counts(self, counts: List[DailyUniqueCount]):
        """Merge DailyUniqueCount objects by date and aggregate counts.

        This method allows us to combine a list of DailyUniqueCount objects
        into the existing 'counts' list and user sets, aggregating the counts
        for each date and ensuring that 'counts' contains only unique
        DailyUniqueCount objects with one count per day and the user is counted only
        once in the date range.

        Examples:
            # Initialize DailyUniqueCounts for a date range
            date_range = DatetimeRange(
                since=arrow.get("2023-01-01"),
                until=arrow.get("2023-01-05")
            )
            daily_unique_counts = DailyUniqueCounts.from_range(date_range)

            # Merge new DailyUniqueCount
            new_counts = [
                DailyUniqueCount(date="2023-09-19", count=2, users={"bob", "jane"})
            ]
            daily_unique_counts.merge_counts(new_counts)

        Note:
            When merging `DailyUniqueCount` instances, the merged output will
            be sorted by ascending date.

        """
        self.counts += counts
        self.counts.sort(key=lambda x: x.date)
        self.counts = [
            reduce(lambda x, y: x + y, v)
            for k, v in groupby(self.counts, lambda dc: dc.date)
        ]

        # Only consider the first occurrence of a user along the date range
        users: Set[str] = set()
        self.total = 0
        for count in self.counts:
            count.users = count.users - users
            count.count = len(count.users)
            self.total += count.count
            users |= count.users

    def to_daily_counts(self):
        """Convert DailyUniqueCounts to DailyCounts."""
        counts = [c.to_daily_count() for c in self.counts]
        total = sum(c.count for c in counts)
        return DailyCounts(total=total, counts=counts)


class LTIUser(BaseModel):
    """Model to represent LTI user data."""

    id: str
    email: str


class LTIToken(BaseModel):
    """Model to represent JWT forged in an LTI context."""

    token_type: str
    exp: int
    iat: int
    jti: str
    session_id: str
    consumer_site: str
    course_id: str
    roles: List[LTIRole]
    user: LTIUser
    locale: str
    resource_link_id: str
    resource_link_description: Optional[str]
