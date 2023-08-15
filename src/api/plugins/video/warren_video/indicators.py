""""Warren video indicators."""
import hashlib
import logging

from ralph.backends.http import BaseHTTP
from ralph.backends.http.async_lrs import LRSQuery
from ralph.models.xapi.concepts.constants.video import RESULT_EXTENSION_TIME
from ralph.models.xapi.concepts.verbs.scorm_profile import CompletedVerb
from ralph.models.xapi.concepts.verbs.tincan_vocabulary import DownloadedVerb
from ralph.models.xapi.concepts.verbs.video import PlayedVerb

from warren.conf import settings
from warren.database_manager import PgsqlManager
from warren.base_indicator import BaseIndicator, PreprocessMixin
from warren.filters import DatetimeRange
from warren.models import DailyCount, DailyCounts
from warren_video.conf import settings as video_plugin_settings


logger = logging.getLogger(__name__)


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
        self.computed_indicator: DailyCounts | None = None
        self.uuid = hashlib.sha256(
                "-".join(
                    col for col in [self.video_id, str(self.date_range), str(self.remove_duplicate_actors), self.__class__.__name__]
                ).encode()
            ).hexdigest()

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

    def persist(self) -> None:
        if not settings.IS_PERSISTENCE_ENABLED:
            return

        db_manager = PgsqlManager()
        db_manager.connect()
        db = db_manager.connection
        with db.cursor() as cursor:
            # Insert total of the range
            cursor.execute(
                "INSERT INTO indicator_date_range_events"
                "(indicator_uuid, video_id, range_start, range_end, count) VALUES"
                "(%s, %s, %s, %s, %s) ON CONFLICT DO NOTHING",
                (self.uuid, self.video_id.replace("uuid://", ""), self.date_range.since.isoformat(), self.date_range.until.isoformat(), self.computed_indicator.total)
            )
            logger.debug(f"Successfully saved ${cursor.rowcount} records in date_range_views_count.")

            # Insert daily counts
            for count in self.computed_indicator.counts:
                cursor.execute("INSERT INTO indicator_daily_events"
                               "(indicator_uuid, video_id, date, count)"
                               "VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING", (self.uuid, self.video_id.replace("uuid://", ""), count.date, count.count))
            logger.debug(f"Successfully saved ${cursor.rowcount} records in daily_views_count.")

            db.commit()
        db_manager.disconnect()

    def fetch_persisted_indicator(self):
        """Check if the indicator was already persisted. If so, retrieve the value."""
        if not settings.IS_PERSISTENCE_ENABLED:
            logger.info("Persistence disabled, computing the indicator...")
        else:
            db_manager = PgsqlManager()
            db_manager.connect()
            with db_manager.cursor as cursor:
                cursor.execute(
                    "SELECT * FROM indicator_date_range_events WHERE indicator_uuid = %s",
                    (self.uuid,)
                )
                stored_total = cursor.fetchone()

                cursor.execute(
                    "SELECT * FROM indicator_daily_events WHERE indicator_uuid = %s",
                    (self.uuid,)
                )
                stored_by_day = cursor.fetchall()
                if stored_total and stored_by_day:
                    logger.info("Found computed indicator in DB, retrieving...")
                    self.computed_indicator = DailyCounts(total=stored_total['count'],
                                                          counts=[DailyCount(date=d['date'], count=d['count']) for d in
                                                                  stored_by_day])
                    return True
                else:
                    logger.info("Indicator not found in DB, computing...")
                    return False

    async def compute(self) -> DailyCounts:
        """Fetch statements and computes the current indicator.

        Fetch the statements from the LRS, filter and aggregate them to return the
        number of video events per day.
        """
        if self.fetch_persisted_indicator():
            return self.computed_indicator

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
        self.computed_indicator = daily_counts
        self.persist()
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
