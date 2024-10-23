""""Warren document indicators."""

from typing import TYPE_CHECKING

from ralph.models.xapi.concepts.verbs.tincan_vocabulary import DownloadedVerb
from warren.indicators import BaseDailyEvent, DailyEvent, DailyUniqueEvent

if TYPE_CHECKING:
    _Base = BaseDailyEvent
else:
    _Base = object


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
