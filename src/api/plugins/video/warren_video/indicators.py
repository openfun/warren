""""Warren video indicators."""

import pandas as pd
from ralph.backends.http.async_lrs import LRSQuery
from ralph.models.xapi.concepts.constants.video import RESULT_EXTENSION_TIME
from ralph.models.xapi.concepts.verbs.scorm_profile import CompletedVerb
from ralph.models.xapi.concepts.verbs.tincan_vocabulary import DownloadedVerb
from ralph.models.xapi.concepts.verbs.video import PlayedVerb
from warren.filters import DatetimeRange
from warren.indicators import BaseIndicator
from warren.models import DailyCount, DailyCounts
from warren.utils import pipe
from warren.xapi import StatementsTransformer
from warren_video.conf import settings as video_plugin_settings


class BaseDailyEvent(BaseIndicator):
    """Base Daily Event indicator.

    This class defines a base daily event indicator. Given an event type, a video,
    and a date range, it calculates the total number of events and the number
    of events per day.

    Required: Indicators inheriting from this base class must declare a 'verb_id'
    class attribute with their xAPI verb ID.
    """

    def __init__(
        self,
        video_id: str,
        date_range: DatetimeRange,
        unique: bool,
    ):
        """Instantiate the Daily Event Indicator.

        Args:
            video_id: The ID of the video on which to compute the metric
            date_range: The date range on which to compute the indicator. It has
                2 fields, `since` and `until` which are dates or timestamps that must be
                in ISO format (YYYY-MM-DD, YYYY-MM-DDThh:mm:ss.sss±hh:mm or
                YYYY-MM-DDThh:mm:ss.sssZ")
            unique (bool): If True, filter out rows with duplicate 'actor.uid'.
        """
        self.unique = unique
        self.video_id = video_id
        self.date_range = date_range

    def __init_subclass__(cls, **kwargs):
        """Ensure subclasses have a 'verb_id' class attribute."""
        super().__init_subclass__(**kwargs)
        if not hasattr(cls, "verb_id"):
            raise TypeError("Indicators must declare a 'verb_id' class attribute")

    def get_lrs_query(
        self,
    ) -> LRSQuery:
        """Get the LRS query for fetching required statements."""
        return LRSQuery(
            query={
                "verb": self.verb_id,
                "activity": self.video_id,
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
        number of video events per day.
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


class DailyViews(BaseDailyEvent):
    """Daily Completed Views indicator.

    Calculate the total and daily counts of views.

    Inherit from BaseDailyEvent, which provides functionality for calculating
    indicators based on different xAPI verbs.
    """

    verb_id = PlayedVerb().id

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
                >= video_plugin_settings.VIEWS_COUNT_TIME_THRESHOLD
            )

        return statements[statements.apply(filter_view_duration, axis=1)]


class DailyCompletedViews(BaseDailyEvent):
    """Daily Completed Views indicator.

    Calculate the total and daily counts of completed views.

    Inherit from BaseDailyEvent, which provides functionality for calculating
    indicators based on different xAPI verbs.
    """

    verb_id = CompletedVerb().id


class DailyDownloads(BaseDailyEvent):
    """Daily Downloads indicator.

    Calculate the total and daily counts of downloads.

    Inherit from BaseDailyEvent, which provides functionality for calculating
    indicators based on different xAPI verbs.
    """

    verb_id = DownloadedVerb().id
