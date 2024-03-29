""""Warren video indicators."""

from typing import TYPE_CHECKING, Optional

import pandas as pd
from ralph.backends.data.async_lrs import LRSStatementsQuery
from ralph.models.xapi.concepts.constants.video import RESULT_EXTENSION_TIME
from ralph.models.xapi.concepts.verbs.scorm_profile import CompletedVerb
from ralph.models.xapi.concepts.verbs.tincan_vocabulary import DownloadedVerb
from ralph.models.xapi.concepts.verbs.video import PlayedVerb
from warren.filters import DatetimeRange
from warren.indicators import BaseIndicator, Frames, IncrementalCacheMixin
from warren.models import DailyCount, DailyCounts, DailyUniqueCount, DailyUniqueCounts
from warren.utils import pipe
from warren.xapi import StatementsTransformer

from .conf import settings as video_plugin_settings


class BaseDailyEvent(BaseIndicator, IncrementalCacheMixin):
    """Base Daily Event indicator.

    This class defines a base daily event indicator. Given an event type, a video,
    and a date range, it calculates the total number of events and the number
    of events per day.

    Required: Indicators inheriting from this base class must declare a 'verb_id'
    class attribute with their xAPI verb ID.
    """

    frame: Frames = "day"
    verb_id: Optional[str] = None
    video_id: str

    def __init__(
        self,
        video_id: str,
        span_range: DatetimeRange,
    ):
        """Instantiate the Daily Event Indicator.

        Args:
            video_id: The ID of the video on which to compute the metric
            span_range: The date range on which to compute the indicator. It has
                2 fields, `since` and `until` which are dates or timestamps that must be
                in ISO format (YYYY-MM-DD, YYYY-MM-DDThh:mm:ss.sss±hh:mm or
                YYYY-MM-DDThh:mm:ss.sssZ")
        """
        super().__init__(span_range=span_range, video_id=video_id)

    def get_lrs_query(
        self,
    ) -> LRSStatementsQuery:
        """Get the LRS query for fetching required statements."""
        return LRSStatementsQuery(
            verb=self.verb_id,
            activity=self.video_id,
            since=self.since,
            until=self.until,
        )

    def filter_statements(self, statements: pd.DataFrame) -> pd.DataFrame:
        """Filter statements required for this indicator.

        This method may be overridden for indicator-specific filtering.
        """
        return statements

    def to_span_range_timezone(self, statements: pd.DataFrame) -> pd.DataFrame:
        """Convert 'timestamps' column to the DatetimeRange's timezone."""
        statements = statements.copy()
        statements["timestamp"] = statements["timestamp"].dt.tz_convert(
            self.span_range.tzinfo
        )
        return statements

    @staticmethod
    def extract_date_from_timestamp(statements: pd.DataFrame) -> pd.DataFrame:
        """Convert the 'timestamp' column to a 'date' column with its date values."""
        statements = statements.copy()
        statements["date"] = statements["timestamp"].dt.date
        statements.drop(["timestamp"], axis=1, inplace=True)
        return statements


class DailyEvent(BaseDailyEvent):
    """Daily Event indicator.

    Required: Indicators inheriting from this base class must declare a 'verb_id'
    class attribute with their xAPI verb ID.
    """

    def __init_subclass__(cls, **kwargs):
        """Ensure subclasses have a 'verb_id' class attribute."""
        super().__init_subclass__(**kwargs)
        if cls.verb_id is None:
            raise TypeError("Indicators must declare a 'verb_id' class attribute")

    async def compute(self) -> DailyCounts:
        """Fetch statements and computes the current indicator.

        Fetch the statements from the LRS, filter and aggregate them to return the
        number of video events per day.
        """
        # Initialize daily counts within the specified date range,
        # with counts equal to zero
        daily_counts = DailyCounts.from_range(self.since, self.until)

        raw_statements = await self.fetch_statements()
        if not raw_statements:
            return daily_counts
        statements = pipe(
            StatementsTransformer.preprocess,
            self.filter_statements,
            self.to_span_range_timezone,
            self.extract_date_from_timestamp,
        )(raw_statements)

        # Compute daily counts from 'statements' DataFrame
        # and merge them into the 'daily_counts' object
        daily_counts.merge_counts(
            [
                DailyCount(date=date, count=count)
                for date, count in statements.groupby("date").size().items()
            ]
        )
        return daily_counts

    @staticmethod
    def merge(a: DailyCounts, b: DailyCounts) -> DailyCounts:
        """Merging function for computed indicators."""
        a.merge_counts(b.counts)
        return a


class DailyUniqueEvent(BaseDailyEvent):
    """Daily Unique Event indicator.

    This class defines a base unique daily event indicator. Given an event
    type, a video, and a date range, it calculates the total number of unique
    user events and the number of unique user events per day.
    """

    def __init_subclass__(cls, **kwargs):
        """Ensure subclasses have a 'verb_id' class attribute."""
        super().__init_subclass__(**kwargs)
        if cls.verb_id is None:
            raise TypeError("Indicators must declare a 'verb_id' class attribute")

    def filter_statements(self, statements: pd.DataFrame) -> pd.DataFrame:
        """Filter statements required for this indicator.

        If necessary, this method removes any duplicate actors from the statements.
        This filtering step is typically done to ensure that each actor's
        contributions are counted only once.
        """
        return statements.drop_duplicates(subset="actor.uid")

    async def compute(self) -> DailyUniqueCounts:
        """Fetch statements and computes the current indicator.

        Fetch the statements from the LRS, filter and aggregate them to return the
        number of unique video events per day.
        """
        # Initialize daily unique counts within the specified date range,
        # with counts equal to zero
        daily_unique_counts = DailyUniqueCounts.from_range(self.since, self.until)

        raw_statements = await self.fetch_statements()
        if not raw_statements:
            return daily_unique_counts

        statements = pipe(
            StatementsTransformer.preprocess,
            self.filter_statements,
            self.to_span_range_timezone,
            self.extract_date_from_timestamp,
        )(raw_statements)

        counts = []
        for date, users in statements.groupby("date")["actor.uid"].unique().items():
            counts.append(
                DailyUniqueCount(date=date, count=len(users), users=set(users))
            )
        daily_unique_counts.merge_counts(counts)

        return daily_unique_counts

    @staticmethod
    def merge(a: DailyUniqueCounts, b: DailyUniqueCounts) -> DailyUniqueCounts:
        """Merging function for computed indicators."""
        a.merge_counts(b.counts)
        return a


if TYPE_CHECKING:
    _Base = BaseDailyEvent
else:
    _Base = object


class DailyViewsMixin(_Base):
    """Daily Views mixin.

    Calculate the total and daily counts of views.
    """

    def filter_statements(self, statements: pd.DataFrame) -> pd.DataFrame:
        """Filter view statements based on additional conditions.

        This method filters the view statements inherited from the base indicator.
        In addition to the base filtering, view statements are further filtered
        based on their duration to match a minimum viewing threshold.
        """
        statements = super().filter_statements(statements)

        def filter_view_duration(row):
            return (
                row[f"result.extensions.{RESULT_EXTENSION_TIME}"]
                <= video_plugin_settings.VIEWS_COUNT_TIME_THRESHOLD
            )

        return statements[statements.apply(filter_view_duration, axis=1)]


class DailyViews(DailyViewsMixin, DailyEvent):
    """Daily Views indicator.

    Calculate the total and daily counts of views.

    Inherit from DailyEvent, which provides functionality for calculating
    indicators based on different xAPI verbs.
    """

    verb_id: str = PlayedVerb().id


class DailyUniqueViews(DailyViewsMixin, DailyUniqueEvent):
    """Daily Unique Views indicator.

    Calculate the total, unique and daily counts of views.

    Inherit from DailyUniqueEvent, which provides functionality for calculating
    indicators based on different xAPI verbs and users.
    """

    verb_id: str = PlayedVerb().id


class DailyCompletedViews(DailyEvent):
    """Daily Completed Views indicator.

    Calculate the total and daily counts of completed views.

    Inherit from DailyEvent, which provides functionality for calculating
    indicators based on different xAPI verbs.
    """

    verb_id: str = CompletedVerb().id


class DailyUniqueCompletedViews(DailyUniqueEvent):
    """Daily Unique Completed Views indicator.

    Calculate the total, unique and daily counts of completed views.

    Inherit from DailyUniqueEvent, which provides functionality for calculating
    indicators based on different xAPI verbs and users.
    """

    verb_id: str = CompletedVerb().id


class DailyDownloads(DailyEvent):
    """Daily Downloads indicator.

    Calculate the total and daily counts of downloads.

    Inherit from DailyEvent, which provides functionality for calculating
    indicators based on different xAPI verbs.
    """

    verb_id: str = DownloadedVerb().id


class DailyUniqueDownloads(DailyUniqueEvent):
    """Daily Unique Downloads indicator.

    Calculate the total, unique and daily counts of downloads.

    Inherit from DailyUniqueEvent, which provides functionality for calculating
    indicators based on different xAPI verbs and users.
    """

    verb_id: str = DownloadedVerb().id
