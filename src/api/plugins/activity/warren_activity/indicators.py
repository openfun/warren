"""Warren activity indicators."""

import pandas as pd

from ralph.backends.http.async_lrs import LRSQuery
from warren.filters import DatetimeRange
from warren.indicators import BaseIndicator
from warren.models import DailyCount, DailyCounts
from warren.utils import pipe
from warren.xapi import StatementsTransformer


class BaseDailyActivity(BaseIndicator):
    """indicator.

    This class defines a base daily event indicator. Given an event type, a video,
    and a date range, it calculates the total number of events and the number
    of events per day.
    """

    def __init__(
        self,
        activity_id: str,
        date_range: DatetimeRange,
        unique: bool,
    ):
        """Instantiate the BaseDailyActivity indicator.

        Args:
            activity_id: The ID of the activity on which to compute the metric.
            date_range: The date range on which to compute the indicator. It has
                2 fields, `since` and `until` which are dates or timestamps that must be
                in ISO format (YYYY-MM-DD, YYYY-MM-DDThh:mm:ss.sss±hh:mm or
                YYYY-MM-DDThh:mm:ss.sssZ")
            unique (bool): If True, filter out rows with duplicate 'actor.uid'.
        """
        self.unique = unique
        self.activity_id = activity_id
        self.date_range = date_range

    def get_lrs_query(self) -> LRSQuery:
        """Get the LRS query for fetching required statements."""
        return LRSQuery(
            query={
                "activity": self.activity_id,
                "since": self.date_range.since.isoformat(),
                "until": self.date_range.until.isoformat(),
            }
        )

    def filter_statements(self, statements: pd.DataFrame) -> pd.DataFrame:
        """Filter statements required for this indicator.

        If necessary, this method removes any duplicate actors from the statements.
        This filtering step is typically done to ensure that each actor's
        contributions are counted only once.
        """
        if self.unique:
            return statements.drop_duplicates(subset="actor.uid")
        return statements

    async def compute(self) -> DailyCounts:
        """Fetch statements and computes the current indicator.

        Fetch the statements from the LRS, filter and aggregate them to return the
        number of events per day.
        """
        # Initialize daily counts within the specified date range,
        # with counts equal to zero
        daily_counts = DailyCounts.from_range(self.date_range)
        statements = await self.fetch_statements()

        if not statements:
            return daily_counts

        statements = pipe(
            StatementsTransformer.preprocess,
            self.filter_statements,
        )(statements)

        # Compute daily counts from 'statements' DataFrame
        # and merge them into the 'daily_counts' object
        daily_counts.merge_counts(
            [
                DailyCount(date=date, count=count)
                for date, count in statements.groupby("date").size().items()
            ]
        )
        return daily_counts
        

class StudentDailyActivity(BaseDailyActivity):
    """"""
    
    def __init__(self, student_ifi: str):
        """"""
        super().__init__()
        self.student_ifi = student_ifi

    def get_lrs_query(self) -> LRSQuery:
        """Get the LRS query for fetching required statements."""
        return LRSQuery(
            query={
                "activity": self.activity_id,
                "actor": self.student_ifi,
                "since": self.date_range.since.isoformat(),
                "until": self.date_range.until.isoformat(),
            }
        )
    

class CohortDailyActivity(BaseDailyActivity):
    """"""

    async def compute(self): 
        """Fetch statements and computes the current indicator.

        Fetch the statements from the LRS, filter and aggregate them to return the
        number of events per day.
        """
        # Initialize daily counts within the specified date range,
        # with counts equal to zero
        daily_counts = DailyCounts.from_range(self.date_range)
        statements = await self.fetch_statements()

        if not statements:
            return daily_counts

        statements = pipe(
            StatementsTransformer.preprocess,
            self.filter_statements,
        )(statements)

        
        # TODO: group by date and actor.uid
        # inspiration from daily counts 
        # Compute daily counts from 'statements' DataFrame
        # and merge them into the 'daily_counts' object
        # daily_counts.merge_counts(
        #     [
        #         DailyCount(date=date, count=count)
        #         for date, count in statements.groupby("date").size().items()
        #     ]
        # )
        
        return daily_counts