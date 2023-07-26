"""Warren API v1 video router."""
import logging

from fastapi import APIRouter, Depends
from typing_extensions import Annotated  # python <3.9 compat
from warren.backends import lrs_client
from warren.fields import IRI
from warren.filters import BaseQueryFilters, DatetimeRange
from warren.models import DailyCounts, Error, Response, StatusEnum
from warren_video.indicators import (
    DailyCompletedVideoViews,
    DailyVideoDownloads,
    DailyVideoViews,
)

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
) -> Response[DailyCounts]:
    """Number of views for `video_id` in the `since` -> `until` date range."""
    indicator_kwargs = {
        "client": lrs_client,
        "video_id": video_id,
        "date_range": DatetimeRange(since=filters.since, until=filters.until),
        "is_unique": unique,
    }

    if complete:
        indicator = DailyCompletedVideoViews(**indicator_kwargs)
    else:
        indicator = DailyVideoViews(**indicator_kwargs)
    try:
        response = Response[DailyCounts](
            status=StatusEnum.SUCCESS, content=indicator.compute()
        )
    except KeyError as exception:
        logger.error(exception)
        return Response[Error](
            status=StatusEnum.FAILED, content=Error(error_message=str(exception))
        )
    return response


@router.get("/{video_id:path}/downloads")
async def downloads(
    video_id: IRI,
    filters: Annotated[BaseQueryFilters, Depends()],
    unique: bool = False,
) -> Response[DailyCounts]:
    """Number of downloads for `video_id` in the `since` -> `until` date range."""
    indicator = DailyVideoDownloads(
        client=lrs_client,
        video_id=video_id,
        date_range=DatetimeRange(since=filters.since, until=filters.until),
        is_unique=unique,
    )
    try:
        response = Response[DailyCounts](
            status=StatusEnum.SUCCESS, content=indicator.compute()
        )
    except KeyError as exception:
        logger.error(exception)
        return Response[Error](
            status=StatusEnum.FAILED, content=Error(error_message=str(exception))
        )
    return response
