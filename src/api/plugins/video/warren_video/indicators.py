""""Warren video indicators."""

from typing import List

from ralph.backends.http import BaseHTTP
from ralph.backends.http.async_lrs import LRSQuery
from ralph.models.xapi.concepts.constants.video import RESULT_EXTENSION_TIME
from ralph.models.xapi.concepts.verbs.scorm_profile import CompletedVerb
from ralph.models.xapi.concepts.verbs.tincan_vocabulary import DownloadedVerb
from ralph.models.xapi.concepts.verbs.video import PlayedVerb
from warren.base_indicator import BaseIndicator, pre_process_statements
from warren.filters import DatetimeRange
from warren.models import XAPI_STATEMENT, DailyCount, DailyCounts
from warren_video.conf import settings as video_plugin_settings


class DailyVideoViews(BaseIndicator):
    """Daily Video Views indicator.

    Defines the daily video views indicator. It is, for a given video, and
    a date range, the total number of views, and the number of views per day.
    """

    def __init__(
        self,
        client: BaseHTTP,
        video_id: str,
        date_range: DatetimeRange,
        is_unique: bool,
    ):
        """Instantiate the indicator with its parameters.

        Args:
            client: The LRS backend to query
            video_id: The ID of the video on which to compute the metric
            date_range: The date range on which to compute the indicator. It has
                2 fields, `since` and `until` which are dates or timestamps that must be
                in ISO format (YYYY-MM-DD, YYYY-MM-DDThh:mm:ss.sss±hh:mm or
                YYYY-MM-DDThh:mm:ss.sssZ")
            is_unique: If true, multiple views by the same actor are counted as
                one
        """
        self.client = client
        self.video_id = video_id
        self.date_range = date_range
        self.is_unique = is_unique

    def get_lrs_query(self) -> LRSQuery:
        """Returns the LRS query for fetching required statements."""
        return LRSQuery(
            query={
                "verb": PlayedVerb().id,
                "activity": self.video_id,
                "since": self.date_range.since.isoformat(),
                "until": self.date_range.until.isoformat(),
            }
        )

    async def fetch_statements(self) -> List[XAPI_STATEMENT]:
        """Executes the LRS query to obtain statements required for this indicator."""
        return [
            value
            async for value in self.client.read(
                target=self.client.statements_endpoint, query=self.get_lrs_query()
            )
        ]

    async def compute(self) -> DailyCounts:
        """Fetches statements and computes the current indicator.

        Fetches the statements from the LRS, filters and aggregates them to return the
        number of video views per day.
        """
        # Initialize daily counts within the specified date range,
        # with counts initialized to zero
        daily_counts = DailyCounts.from_range(self.date_range)
        raw_statements = await self.fetch_statements()
        if not raw_statements:
            return daily_counts
        flattened = pre_process_statements(raw_statements)

        # Filter out video played events before the configured time threshold
        def filter_view_duration(row):
            return (
                row[f"result.extensions.{RESULT_EXTENSION_TIME}"]
                >= video_plugin_settings.VIEWS_COUNT_TIME_THRESHOLD
            )

        # Apply the filtering function to each row
        filtered_view_duration = flattened[
            flattened.apply(filter_view_duration, axis=1)
        ]

        # Filter out duplicate 'actor.uid' if 'is_unique' is selected.
        if self.is_unique:
            filtered_view_duration.drop_duplicates(subset="actor.uid", inplace=True)

        # Compute daily counts from 'filtered_view_duration' DataFrame
        # and merge them into the 'indicator' DailyCounts object
        daily_counts.merge_counts(
            [
                DailyCount(date=date, count=count)
                for date, count in filtered_view_duration.groupby("date").size().items()
            ]
        )
        return daily_counts


class DailyCompletedVideoViews(BaseIndicator):
    """Daily Completed Video Views indicator.

    For a given video, and a date range, this indicator computes the total number
    of `completed` views events, and the number of views per day.
    """

    def __init__(
        self,
        client: BaseHTTP,
        video_id: str,
        date_range: DatetimeRange,
        is_unique: bool,
    ):
        """Instantiate the indicator with its parameters.

        Args:
            client: The LRS backend from which the query is to be issued
            video_id: The ID of the video on which to compute the metric
            date_range: The date range on which to compute the indicator. It has
                2 fields, `since` and `until` which are dates or timestamps that must be
                in ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:mm:ss.SSSZ")
            is_unique: If true, multiple views by the same actor are counted as
                one
        """
        self.client = client
        self.video_id = video_id
        self.date_range = date_range
        self.is_unique = is_unique

    def get_lrs_query(self) -> LRSQuery:
        """Returns the LRS query for fetching required statements."""
        return LRSQuery(
            query={
                "verb": CompletedVerb().id,
                "activity": self.video_id,
                "since": self.date_range.since.isoformat(),
                "until": self.date_range.until.isoformat(),
            }
        )

    async def fetch_statements(self) -> List[XAPI_STATEMENT]:
        """Executes the LRS query to obtain statements required for this indicator."""
        return [
            value
            async for value in self.client.read(
                target=self.client.statements_endpoint, query=self.get_lrs_query()
            )
        ]

    async def compute(self) -> DailyCounts:
        """Fetches statements and computes the current indicator.

        Fetches the statements from the LRS, filters and aggregates them to return the
        number of video views per day.
        """
        # Initialize daily counts within the specified date range,
        # with counts initialized to zero
        daily_counts = DailyCounts.from_range(self.date_range)
        raw_statements = await self.fetch_statements()

        if not raw_statements:
            return daily_counts
        flattened = pre_process_statements(raw_statements)

        # Filter out duplicate 'actor.uid' if 'is_unique' is selected.
        if self.is_unique:
            flattened.drop_duplicates(subset="actor.uid", inplace=True)

        # Compute daily counts from 'flattened' DataFrame
        # and merge them into the 'indicator' DailyCounts object
        daily_counts.merge_counts(
            [
                DailyCount(date=date, count=count)
                for date, count in flattened.groupby("date").size().items()
            ]
        )
        return daily_counts


class DailyVideoDownloads(BaseIndicator):
    """Daily Video Downloads indicator.

    Defines the daily video downloads indicator. It is, for a given video, and
    a date range, the total number of downloads, and the number of downloads per day.
    """

    def __init__(
        self,
        client: BaseHTTP,
        video_id: str,
        date_range: DatetimeRange,
        is_unique: bool,
    ):
        """Instantiate the indicator with its parameters.

        Args:
            client: The LRS backend to query
            video_id: The ID of the video on which to compute the metric
            date_range: The date range on which to compute the indicator. It has
                2 fields, `since` and `until` which are dates or timestamps that must be
                in ISO format (YYYY-MM-DD, YYYY-MM-DDThh:mm:ss.sss±hh:mm or
                YYYY-MM-DDThh:mm:ss.sssZ")
            is_unique: If true, multiple downloads by the same actor are counted as one
        """
        self.client = client
        self.video_id = video_id
        self.date_range = date_range
        self.is_unique = is_unique

    def get_lrs_query(self) -> LRSQuery:
        """Returns the LRS query for fetching required statements."""
        return LRSQuery(
            query={
                "verb": DownloadedVerb().id,
                "activity": self.video_id,
                "since": self.date_range.since.isoformat(),
                "until": self.date_range.until.isoformat(),
            }
        )

    async def fetch_statements(self) -> List[XAPI_STATEMENT]:
        """Executes the LRS query to obtain statements required for this indicator."""
        return [
            value
            async for value in self.client.read(
                target=self.client.statements_endpoint, query=self.get_lrs_query()
            )
        ]

    async def compute(self) -> DailyCounts:
        """Fetches statements and computes the current indicator.

        Fetches the statements from the LRS, filters and aggregates them to return the
        number of video downloads per day.
        """
        # Initialize daily counts within the specified date range,
        # with counts initialized to zero
        daily_counts = DailyCounts.from_range(self.date_range)
        raw_statements = await self.fetch_statements()
        if not raw_statements:
            return daily_counts
        preprocessed_statements = pre_process_statements(raw_statements)

        # Filter out duplicate 'actor.uid' if 'is_unique' is selected.
        if self.is_unique:
            preprocessed_statements.drop_duplicates(subset="actor.uid", inplace=True)

        # Compute daily counts from 'preprocessed_statements' DataFrame
        # and merge them into the 'indicator' DailyCounts object
        daily_counts.merge_counts(
            [
                DailyCount(date=date, count=count)
                for date, count in preprocessed_statements.groupby("date")
                .size()
                .items()
            ]
        )
        return daily_counts
