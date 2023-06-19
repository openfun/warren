"""Reusable statement filters."""
from typing import Dict

from ralph.models.xapi.concepts.constants.video import RESULT_EXTENSION_TIME
from warren_video.conf import settings as video_settings


def filter_played_views(statement: Dict):
    """Do not count video played less than the configured time."""
    return (
        statement["result"]["extensions"][RESULT_EXTENSION_TIME]
        < video_settings.VIEWS_COUNT_TIME_THRESHOLD
    )
