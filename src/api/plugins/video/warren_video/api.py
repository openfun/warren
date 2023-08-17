"""Warren API v1 video router."""
import logging

from fastapi import APIRouter, Depends, BackgroundTasks
from typing_extensions import Annotated  # python <3.9 compat

from warren.backends import lrs_client
from warren.fields import IRI
from warren.filters import BaseQueryFilters, DatetimeRange
from warren.models import DailyCounts, Error, Response, StatusEnum
from warren_video.indicators import DailyCompletedViews, DailyDownloads, DailyViews

router = APIRouter(
    prefix="/video",
)

logger = logging.getLogger(__name__)


@router.get("/{video_id:path}/views")
async def views(
    background_tasks: BackgroundTasks,
    video_id: IRI,
    filters: Annotated[BaseQueryFilters, Depends()],
    complete: bool = False,
    unique: bool = False,
) -> Response[DailyCounts]:
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
        response = Response[DailyCounts](
            status=StatusEnum.SUCCESS, content=await indicator.compute()
        )
        background_tasks.add_task(indicator.persist)
    except (KeyError, AttributeError) as exception:
        logger.error(exception)
        response = Response[Error](
            status=StatusEnum.FAILED, content=Error(error_message=str(exception))
        )

    return response


@router.get("/{video_id:path}/downloads")
async def downloads(
    background_tasks: BackgroundTasks,
    video_id: IRI,
    filters: Annotated[BaseQueryFilters, Depends()],
    unique: bool = False,
) -> Response[DailyCounts]:
    """Number of downloads for `video_id` in the `since` -> `until` date range."""
    indicator = DailyDownloads(
        client=lrs_client,
        video_id=video_id,
        date_range=DatetimeRange.parse_obj(filters),
        remove_duplicate_actors=unique,
    )

    try:
        response = Response[DailyCounts](
            status=StatusEnum.SUCCESS, content=await indicator.compute()
        )
        background_tasks.add_task(indicator.persist)
    except (KeyError, AttributeError) as exception:
        logger.error(exception)
        response = Response[Error](
            status=StatusEnum.FAILED, content=Error(error_message=str(exception))
        )

    return response
