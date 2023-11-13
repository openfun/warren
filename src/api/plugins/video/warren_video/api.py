"""Warren API v1 video router."""
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from typing_extensions import Annotated  # python <3.9 compat
from warren.exceptions import LrsClientException
from warren.fields import IRI
from warren.filters import BaseQueryFilters, DatetimeRange
from warren.models import DailyCounts, DailyUniqueCounts, LTIToken
from warren.utils import get_lti_token
from warren_video.indicators import (
    DailyCompletedViews,
    DailyDownloads,
    DailyUniqueCompletedViews,
    DailyUniqueDownloads,
    DailyUniqueViews,
    DailyViews,
)

router = APIRouter(
    prefix="/video",
)

logger = logging.getLogger(__name__)


@router.get("/{video_id:path}/views")
async def views(
    video_id: IRI,
    filters: Annotated[BaseQueryFilters, Depends()],
    token: Annotated[LTIToken, Depends(get_lti_token)],
    complete: bool = False,
    unique: bool = False,
) -> DailyCounts:
    """Number of views for `video_id` in the `since` -> `until` date range."""
    # Switch/case pattern matching with the (complete, unique) boolean tuple
    logger.debug("Start computing 'views' indicator")
    klass_mapping = {
        (True, True): DailyUniqueCompletedViews,
        (True, False): DailyCompletedViews,
        (False, True): DailyUniqueViews,
        (False, False): DailyViews,
    }
    indicator = klass_mapping.get((complete, unique), DailyViews)(
        video_id=video_id, span_range=DatetimeRange.parse_obj(filters)
    )
    logger.debug("Will compute indicator %s", type(indicator).__name__)
    logger.debug(
        "From %s to %s", indicator.span_range.since, indicator.span_range.until
    )

    try:
        results = await indicator.get_or_compute()
    except (KeyError, AttributeError, LrsClientException) as exception:
        message = "An error occurred while computing the number of views"
        logger.exception("%s. Exception:", message)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=message
        ) from exception

    if isinstance(results, DailyUniqueCounts):
        results = results.to_daily_counts()
    logger.debug("Results = %s", results)
    logger.debug("Finish computing 'views' indicator")
    return results


@router.get("/{video_id:path}/downloads")
async def downloads(
    video_id: IRI,
    filters: Annotated[BaseQueryFilters, Depends()],
    token: Annotated[LTIToken, Depends(get_lti_token)],
    unique: bool = False,
) -> DailyCounts:
    """Number of downloads for `video_id` in the `since` -> `until` date range."""
    logger.debug("Start computing 'downloads' indicator")
    indicator_klass = DailyUniqueDownloads if unique else DailyDownloads
    indicator = indicator_klass(
        video_id=video_id, span_range=DatetimeRange.parse_obj(filters)
    )
    logger.debug("Will compute indicator %s", type(indicator).__name__)
    logger.debug(
        "From %s to %s", indicator.span_range.since, indicator.span_range.until
    )

    try:
        results = await indicator.get_or_compute()
    except (KeyError, AttributeError, LrsClientException) as exception:
        message = "An error occurred while computing the number of downloads"
        logger.exception("%s. Exception:", message)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=message
        ) from exception

    if isinstance(results, DailyUniqueCounts):
        results = results.to_daily_counts()
    logger.debug("Results = %s", results)
    logger.debug("Finish computing 'downloads' indicator")
    return results
