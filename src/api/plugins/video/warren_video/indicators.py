""""Warren video indicators."""

from typing import TYPE_CHECKING

import pandas as pd
from ralph.models.xapi.concepts.constants.video import RESULT_EXTENSION_TIME
from ralph.models.xapi.concepts.verbs.scorm_profile import CompletedVerb
from ralph.models.xapi.concepts.verbs.tincan_vocabulary import DownloadedVerb
from ralph.models.xapi.concepts.verbs.video import PlayedVerb
from warren.indicators import BaseDailyEvent, DailyEvent, DailyUniqueEvent

from .conf import settings as video_plugin_settings

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
