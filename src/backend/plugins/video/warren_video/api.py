"""Warren API v1 video router."""
import logging

from fastapi import APIRouter, Depends
from typing_extensions import Annotated  # python <3.9 compat
from warren.backends import lrs_client
from warren.fields import IRI
from warren.filters import BaseQueryFilters, DatetimeRange
from warren.models import Error, Response, StatusEnum
from warren_video.indicators.daily_video_views import DailyVideoViewsIndicator
from warren_video.indicators.unique_views_count import UniqueViewsCountIndicator
from warren_video.models import DailyVideoViews, UniqueViewsCount

router = APIRouter(
    prefix="/video",
)

logger = logging.getLogger(__name__)


@router.get("/{video_uuid:path}/views")
async def views(
    video_uuid: IRI,
    filters: Annotated[BaseQueryFilters, Depends()],
    complete: bool = False,
) -> Response[DailyVideoViews]:
    """Daily views count for `video_uuid` in the `since` -> `until` date range.

    Args:
        video_uuid: The UUID of the video on which to compute the metric
        filters: The basic query filters, including date range.
        complete: If true, count `Completed` events instead of `Played` events
    """
    indicator = DailyVideoViewsIndicator(
        client=lrs_client,
        video_uuid=video_uuid,
        date_range=DatetimeRange(since=filters.since, until=filters.until),
        is_completed_views=complete,
    )
    try:
        response = Response[DailyVideoViews](
            status=StatusEnum.SUCCESS, content=indicator.compute()
        )
    except KeyError as exception:
        logger.error(exception)
        return Response[Error](
            status=StatusEnum.FAILED, content=Error(error_message=str(exception))
        )
    return response


@router.get("/{video_uuid:path}/viewers")
async def viewers(
    video_uuid: IRI,
    filters: Annotated[BaseQueryFilters, Depends()],
    complete: bool = False,
) -> Response[UniqueViewsCount]:
    """Total number of unique views for `video_uuid` in the `since` -> `until` date range.

    Args:
        video_uuid: The UUID of the video on which to compute the metric
        filters: The basic query filters, including date range.
        complete: If true, count `Completed` events instead of `Played` events
    """
    indicator = UniqueViewsCountIndicator(
        client=lrs_client,
        video_uuid=video_uuid,
        date_range=DatetimeRange(since=filters.since, until=filters.until),
        is_completed_views=complete,
    )
    try:
        response = Response[UniqueViewsCount](
            status=StatusEnum.SUCCESS, content=indicator.compute()
        )
    except KeyError as exception:
        logger.error(exception)
        return Response[Error](
            status=StatusEnum.FAILED, content=Error(error_message=str(exception))
        )
    return response
