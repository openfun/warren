"""Warren API v1 video router."""
import logging

from fastapi import APIRouter, Depends, HTTPException
from typing_extensions import Annotated  # python <3.9 compat
from warren.backends import lrs_client
from warren.fields import IRI
from warren.filters import BaseQueryFilters, DatetimeRange
from warren.models import DailyCounts
from warren_video.indicators import DailyCompletedViews, DailyDownloads, DailyViews, Wip
from warren_video.models import Info

router = APIRouter(
    prefix="/video",
)

logger = logging.getLogger(__name__)


@router.get("/{video_id:path}/views")
async def views(
    video_id: IRI,
    filters: Annotated[BaseQueryFilters, Depends()],
    complete: bool = False,
    unique: bool = False,
) -> DailyCounts:
    """Number of views for `video_id` in the `since` -> `until` date range."""
    indicator_kwargs = {
        "client": lrs_client,
        "video_id": video_id,
        "date_range": DatetimeRange.parse_obj(filters),
        "remove_duplicate_actors": unique,
    }

    if complete:
        indicator = DailyCompletedViews(**indicator_kwargs)
    else:
        indicator = DailyViews(**indicator_kwargs)

    try:
        return await indicator.compute()
    except (KeyError, AttributeError) as exception:
        message = "An error occurred while computing the number of views"
        logger.error("%s: %s", message, exception)
        raise HTTPException(status_code=500, detail=message) from exception


@router.get("/{video_id:path}/downloads")
async def downloads(
    video_id: IRI,
    filters: Annotated[BaseQueryFilters, Depends()],
    unique: bool = False,
) -> DailyCounts:
    """Number of downloads for `video_id` in the `since` -> `until` date range."""
    indicator = DailyDownloads(
        client=lrs_client,
        video_id=video_id,
        date_range=DatetimeRange.parse_obj(filters),
        remove_duplicate_actors=unique,
    )

    try:
        return await indicator.compute()
    except (KeyError, AttributeError) as exception:
        message = "An error occurred while computing the number of downloads"
        logger.error("%s: %s", message, exception)
        raise HTTPException(status_code=500, detail=message) from exception


@router.get("/{video_id:path}/info")
async def info(
    video_id: IRI,
) -> Info:
    """Wip."""
    indicator = Wip(
        client=lrs_client,
        video_id=video_id,
    )
    try:
        return await indicator.compute()
    # todo - specify this exception handling
    except Exception as exception:
        message = "An error occurred while computing the information"
        logger.error("%s: %s", message, exception)
        raise HTTPException(status_code=500, detail=message) from exception
