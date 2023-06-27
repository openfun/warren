"""Warren API v1 video router."""
import logging

from fastapi import APIRouter, Depends
from typing_extensions import Annotated  # python <3.9 compat
from warren.backends import lrs_client
from warren.fields import IRI
from warren.filters import BaseQueryFilters, DatetimeRange
from warren.models import Error, Response, StatusEnum
from warren_video.indicators import DailyVideoViews
from warren_video.models import VideoViews

router = APIRouter(
    prefix="/video",
)

logger = logging.getLogger(__name__)


@router.get("/{video_uuid:path}/views")
async def views(
    video_uuid: IRI, filters: Annotated[BaseQueryFilters, Depends()]
) -> Response[VideoViews]:
    """Number of views for `video_uuid` in the `since` -> `until` date range."""
    indicator = DailyVideoViews(
        client=lrs_client,
        video_uuid=video_uuid,
        date_range=DatetimeRange(since=filters.since, until=filters.until),
    )
    try:
        response = Response[VideoViews](
            status=StatusEnum.SUCCESS, content=indicator.compute()
        )
    except KeyError as exception:
        logger.error(exception)
        return Response[Error](
            status=StatusEnum.FAILED, content=Error(error_message=str(exception))
        )
    return response
