""""Warren video indicators."""

from typing import List

from ralph.backends.http.lrs import BaseHTTP, LRSQuery
from ralph.models.xapi.concepts.constants.video import RESULT_EXTENSION_TIME
from ralph.models.xapi.concepts.verbs.scorm_profile import CompletedVerb
from ralph.models.xapi.concepts.verbs.video import PlayedVerb
from warren.base_indicator import BaseIndicator, pre_process_statements
from warren.filters import DatetimeRange
from warren.models import XAPI_STATEMENT
from warren_video.conf import settings as video_plugin_settings
from warren_video.models import VideoViews


class DailyVideoViews(BaseIndicator):
    """Daily Video Views indicator.

    Defines the daily video views indicator. It is, for a given video, and
    a date range, the total number of views, and the number of views per day.
    """

    def __init__(
        self,
        client: BaseHTTP,
        video_uuid: str,
        date_range: DatetimeRange,
        is_unique: bool,
    ):
        """Instantiate the indicator with its parameters.

        Args:
            client: The LRS backend to query
            video_uuid: The UUID of the video on which to compute the metric
            date_range: The date range on which to compute the indicator. It has
                2 fields, `since` and `until` which are dates or timestamps that must be
                in ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:mm:ss.SSSZ")
            is_unique: If true, multiple views by the same actor are counted as
                one
        """
        self.client = client
        self.video_uuid = video_uuid
        self.date_range = date_range
        self.is_unique = is_unique

    def get_lrs_query(self) -> LRSQuery:
        """Returns the LRS query for fetching required statements."""
        return LRSQuery(
            query={
                "verb": PlayedVerb().id,
                "activity": self.video_uuid,
                "since": self.date_range.since.isoformat(),
                "until": self.date_range.until.isoformat(),
            }
        )

    def fetch_statements(self) -> List[XAPI_STATEMENT]:
        """Executes the LRS query to obtain statements required for this indicator."""
        return list(
            self.client.read(
                target=self.client.statements_endpoint, query=self.get_lrs_query()
            )
        )

    def compute(self) -> VideoViews:
        """Fetches statements and computes the current indicator.

        Fetches the statements from the LRS, filters and aggregates them to return the
        number of video views per day.
        """
        indicator = VideoViews()
        raw_statements = self.fetch_statements()
        if not raw_statements:
            return indicator
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

        # If the `is_unique` filter is selected, filter out rows with duplicate
        # `actor.account.name`
        if self.is_unique:
            filtered_view_duration.drop_duplicates(subset="actor.uuid", inplace=True)

        # Group by day and calculate sum of events per day
        count_by_date = (
            filtered_view_duration.groupby(filtered_view_duration["date"])
            .count()
            .reset_index()
            .rename(columns={"id": "count"})
            .loc[:, ["date", "count"]]
        )

        # Calculate the total number of events
        indicator.total_views = len(filtered_view_duration.index)
        indicator.count_by_date = count_by_date.to_dict("records")

        return indicator


class DailyCompletedVideoViews(BaseIndicator):
    """Daily Completed Video Views indicator.

    For a given video, and a date range, this indicator computes the total number
    of `completed` views events, and the number of views per day.
    """

    def __init__(
        self,
        client: BaseHTTP,
        video_uuid: str,
        date_range: DatetimeRange,
        is_unique: bool,
    ):
        """Instantiate the indicator with its parameters.

        Args:
            client: The LRS backend from which the query is to be issued
            video_uuid: The UUID of the video on which to compute the metric
            date_range: The date range on which to compute the indicator. It has
                2 fields, `since` and `until` which are dates or timestamps that must be
                in ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:mm:ss.SSSZ")
            is_unique: If true, multiple views by the same actor are counted as
                one
        """
        self.client = client
        self.video_uuid = video_uuid
        self.date_range = date_range
        self.is_unique = is_unique

    def get_lrs_query(self) -> LRSQuery:
        """Returns the LRS query for fetching required statements."""
        return LRSQuery(
            query={
                "verb": CompletedVerb().id,
                "activity": self.video_uuid,
                "since": self.date_range.since.isoformat(),
                "until": self.date_range.until.isoformat(),
            }
        )

    def fetch_statements(self) -> List[XAPI_STATEMENT]:
        """Executes the LRS query to obtain statements required for this indicator."""
        return list(
            self.client.read(
                target=self.client.statements_endpoint, query=self.get_lrs_query()
            )
        )

    def compute(self) -> VideoViews:
        """Fetches statements and computes the current indicator.

        Fetches the statements from the LRS, filters and aggregates them to return the
        number of video views per day.
        """
        indicator = VideoViews()
        raw_statements = self.fetch_statements()
        if not raw_statements:
            return indicator
        flattened = pre_process_statements(raw_statements)

        # If the `is_unique` filter is selected, filter out rows with duplicate
        # `actor.account.name`
        if self.is_unique:
            flattened.drop_duplicates(subset="actor.uuid", inplace=True)

        # Group by day and calculate sum of events per day
        count_by_date = (
            flattened.groupby(flattened["date"])
            .count()
            .reset_index()
            .rename(columns={"id": "count"})
            .loc[:, ["date", "count"]]
        )

        # Calculate the total number of events
        indicator.total_views = len(flattened.index)
        indicator.count_by_date = count_by_date.to_dict("records")  # type: ignore[assignment]

        return indicator
