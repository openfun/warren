""""Warren video indicators."""


from ralph.backends.http import BaseHTTP
from ralph.backends.http.async_lrs import LRSQuery
from ralph.models.xapi.concepts.constants.video import (
    CONTEXT_EXTENSION_COMPLETION_THRESHOLD,
    CONTEXT_EXTENSION_LENGTH,
    RESULT_EXTENSION_TIME,
)
from ralph.models.xapi.concepts.verbs.scorm_profile import (
    CompletedVerb,
    InitializedVerb,
)
from ralph.models.xapi.concepts.verbs.tincan_vocabulary import DownloadedVerb
from ralph.models.xapi.concepts.verbs.video import PlayedVerb
from warren.base_indicator import BaseIndicator, PreprocessMixin
from warren.filters import DatetimeRange
from warren.models import DailyCount, DailyCounts
from warren_video.conf import settings as video_plugin_settings
from warren_video.models import Info


class BaseDailyEvent(BaseIndicator, PreprocessMixin):
    """Base Daily Event indicator.

    This class defines a base daily event indicator. Given an event type, a video,
    and a date range, it calculates the total number of events and the number
    of events per day.
    """

    def __init__(
        self,
        client: BaseHTTP,
        video_id: str,
        date_range: DatetimeRange,
        remove_duplicate_actors: bool,
    ):
        """Instantiate the Daily Event Indicator.

        Args:
            client (BaseHTTP): The LRS backend to query.
            video_id: The ID of the video on which to compute the metric
            date_range: The date range on which to compute the indicator. It has
                2 fields, `since` and `until` which are dates or timestamps that must be
                in ISO format (YYYY-MM-DD, YYYY-MM-DDThh:mm:ss.sss±hh:mm or
                YYYY-MM-DDThh:mm:ss.sssZ")
            remove_duplicate_actors (bool): If True, filter out rows with duplicate
                'actor.uid'.
        """
        self.client = client
        self.remove_duplicate_actors = remove_duplicate_actors
        self.video_id = video_id
        self.date_range = date_range

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

    async def fetch_statements(self) -> None:
        """Execute the LRS query to obtain statements required for this indicator."""
        self.raw_statements = [
            value
            async for value in self.client.read(
                target=self.client.statements_endpoint, query=self.get_lrs_query()
            )
        ]

    def filter_statements(self) -> None:
        """Filter statements required for this indicator.

        If necessary, this method removes any duplicate actors from the statements.
        This filtering step is typically done to ensure that each actor's
        contributions are counted only once.
        """
        if self.remove_duplicate_actors:
            self.statements.drop_duplicates(subset="actor.uid", inplace=True)

    async def compute(self) -> DailyCounts:
        """Fetch statements and computes the current indicator.

        Fetch the statements from the LRS, filter and aggregate them to return the
        number of video events per day.
        """
        # Initialize daily counts within the specified date range,
        # with counts equal to zero
        daily_counts = DailyCounts.from_range(self.date_range)
        await self.fetch_statements()

        if not self.raw_statements:
            return daily_counts

        self.preprocess_statements()
        self.filter_statements()

        # Compute daily counts from 'statements' DataFrame
        # and merge them into the 'daily_counts' object
        daily_counts.merge_counts(
            [
                DailyCount(date=date, count=count)
                for date, count in self.statements.groupby("date").size().items()
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

    def filter_statements(self) -> None:
        """Filter view statements based on additional conditions.

        This method filters the view statements inherited from the base indicator.
        In addition to the base filtering, view statements are further filtered
        based on their duration to match a minimum viewing threshold.
        """
        super().filter_statements()

        def filter_view_duration(row):
            return (
                row[f"result.extensions.{RESULT_EXTENSION_TIME}"]
                >= video_plugin_settings.VIEWS_COUNT_TIME_THRESHOLD
            )

        self.statements = self.statements[
            self.statements.apply(filter_view_duration, axis=1)
        ]


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


class Wip(BaseIndicator, PreprocessMixin):

    def __init__(
        self,
        client: BaseHTTP,
        video_id: str,
    ):
        self.client = client
        self.video_id = video_id

    def get_lrs_query(
        self,
    ) -> LRSQuery:
        """Get the LRS query for fetching required statements."""
        return LRSQuery(
            query={
                "activity": self.video_id,
                "verb": InitializedVerb().id,
            }
        )

    async def fetch_statements(self) -> None:
        """Execute the LRS query to obtain statements required for this indicator."""
        self.raw_statements = [
            value
            async for value in self.client.read(
                target=self.client.statements_endpoint, query=self.get_lrs_query()
            )
        ]

    # todo - discuss whether it makes sense, as we have already loaded all statements.
    def filter_statements(self) -> None:
        self.raw_statements = self.raw_statements.sample(3)

    async def compute(self) -> Info:
        await self.fetch_statements()

        if not self.raw_statements:
            return Info(
                name=None,
                length=None,
                completion_threshold=None,
            )

        self.parse_raw_statements()

        def get_most_common_value(column_name):
            try:
                values = self.statements[column_name].dropna()
                if values.empty:
                    return None
                # Returning the first value is arbitrary.
                return values.mode().iloc[0]
            except KeyError:
                return None

        context_base_string = "context.extensions.{}"

        return Info(
            name=get_most_common_value("object.definition.name.en-US"),
            length=get_most_common_value(
                context_base_string.format(CONTEXT_EXTENSION_LENGTH)
            ),
            completion_threshold=get_most_common_value(
                context_base_string.format(CONTEXT_EXTENSION_COMPLETION_THRESHOLD)
            ),
        )
