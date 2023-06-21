"""Warren API v1 video router."""
import logging
from typing import List, Dict

from fastapi import APIRouter, Depends
from typing_extensions import Annotated  # python <3.9 compat

from warren.backends import lrs_client
from warren.fields import IRI
from warren.filters import BaseQueryFilters
from warren_video.indicators.daily_video_views import DailyVideoViews

router = APIRouter(
    prefix="/video",
)

logger = logging.getLogger(__name__)


@router.get("/{video_id:path}/views")
async def views(
    video_id: IRI, filters: Annotated[BaseQueryFilters, Depends()]
) -> Dict:
    """Number of views for `video_id` in the `since` -> `until` date range."""
    indicator = DailyVideoViews(
        client=lrs_client,
        activity=video_id,
        since=filters.since.isoformat(),
        until=filters.until.isoformat()
    )

    computed_indicator = indicator.compute()

    return computed_indicator
