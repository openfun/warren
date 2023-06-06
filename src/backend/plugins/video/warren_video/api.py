"""Warren API v1 video router."""
import logging
from collections import Counter
from typing import List

import arrow
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from ralph.backends.http.lrs import LRSQuery
from ralph.exceptions import BackendException
from ralph.models.xapi.concepts.constants.video import RESULT_EXTENSION_TIME
from ralph.models.xapi.concepts.verbs.video import PlayedVerb
from starlette import status
from typing_extensions import Annotated  # python <3.9 compat
from warren_video.conf import settings as video_settings

from warren.backends import lrs_client
from warren.conf import settings
from warren.fields import IRI, Date
from warren.filters import BaseQueryFilters

router = APIRouter(
    prefix="/video",
)

logger = logging.getLogger(__name__)


class VideoDayViews(BaseModel):
    """Model to represent video views for a date."""

    day: Date
    views: int = 0


class VideoViews(BaseModel):
    """Model to represent video views."""

    total: int
    daily_views: List[VideoDayViews]


@router.get("/{video_id:path}/views")
async def views(
    video_id: IRI, filters: Annotated[BaseQueryFilters, Depends()]
) -> VideoViews:
    """Video views."""
    query = {
        "verb": PlayedVerb().id,
        "activity": video_id,
        "since": filters.since.isoformat(),
        "until": filters.until.isoformat(),
    }

    try:
        statements = list(
            lrs_client.read(target="/xAPI/statements", query=LRSQuery(query=query))
        )
    except BackendException as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="xAPI statements query failed",
        ) from error

    date_range = [
        d.format(settings.DATE_FORMAT)
        for d in arrow.Arrow.range("day", filters.since, filters.until)
    ]

    def filter_played_statement(statement) -> bool:
        """Do not count video played less than the configured time."""
        return (
            statement["result"]["extensions"][RESULT_EXTENSION_TIME]
            < video_settings.VIEWS_COUNT_TIME_THRESHOLD
        )

    timestamps = [
        arrow.get(statement["timestamp"]).format(settings.DATE_FORMAT)
        for statement in statements
        if filter_played_statement(statement)
    ]

    counter = Counter(timestamps)
    daily_views = [VideoDayViews(day=date, views=counter[date]) for date in date_range]

    return VideoViews(
        total=sum(view.views for view in daily_views), daily_views=daily_views
    )
