"""Warren API v1 video router."""
import logging

from fastapi import APIRouter, Depends, HTTPException
from typing_extensions import Annotated  # python <3.9 compat
from warren.exceptions import LrsClientException
from warren.fields import IRI
from warren.filters import BaseQueryFilters, DatetimeRange
from warren.models import DailyCounts
from warren_video.indicators import DailyCompletedViews, DailyDownloads, DailyViews

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
        "video_id": video_id,
        "date_range": DatetimeRange.parse_obj(filters),
        "unique": unique,
    }

    if complete:
        indicator = DailyCompletedViews(**indicator_kwargs)
    else:
        indicator = DailyViews(**indicator_kwargs)

    try:
        return await indicator.compute()
    except (KeyError, AttributeError, LrsClientException) as exception:
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
        video_id=video_id,
        date_range=DatetimeRange.parse_obj(filters),
        unique=unique,
    )

    try:
        return await indicator.compute()
    except (KeyError, AttributeError, LrsClientException) as exception:
        message = "An error occurred while computing the number of downloads"
        logger.error("%s: %s", message, exception)
        raise HTTPException(status_code=500, detail=message) from exception
