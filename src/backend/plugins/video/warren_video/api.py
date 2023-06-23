"""Warren API v1 video router."""
import logging

from fastapi import APIRouter, Depends
from typing_extensions import Annotated  # python <3.9 compat
from warren_video.indicators.daily_video_views import DailyVideoViews
from warren_video.indicators.models import VideoViews

from warren.backends import lrs_client
from warren.fields import IRI
from warren.filters import BaseQueryFilters, DatetimeRange

router = APIRouter(
    prefix="/video",
)

logger = logging.getLogger(__name__)


@router.get("/{video_uuid:path}/views")
async def views(
    video_uuid: IRI, filters: Annotated[BaseQueryFilters, Depends()]
) -> VideoViews:
    """Number of views for `video_id` in the `since` -> `until` date range."""
    indicator = DailyVideoViews(
        client=lrs_client,
        video_uuid=video_uuid,
        date_range=DatetimeRange(since=filters.since, until=filters.until),
    )
    computed_indicator = indicator.compute()

    return computed_indicator
