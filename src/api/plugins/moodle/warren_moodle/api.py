"""Warren API v1 Moodle router."""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing_extensions import Annotated  # python <3.9 compat
from warren.exceptions import LrsClientException
from warren.filters import BaseQueryFilters, DatetimeRange
from warren.models import DailyCounts, DailyUniqueCounts, LTIToken
from warren.utils import get_lti_course_id, get_lti_token

from .indicators import (
    DailyUniqueViews,
    DailyViews,
)
from .models import ViewsActivities

router = APIRouter(
    prefix="/moodle",
)

logger = logging.getLogger(__name__)


@router.get("/views")
async def views(
    course_id: Annotated[str, Depends(get_lti_course_id)],
    filters: Annotated[BaseQueryFilters, Depends()],
    token: Annotated[LTIToken, Depends(get_lti_token)],
    unique: bool = False,
    activities: List[ViewsActivities] = Query(None),
) -> DailyCounts:
    """Number of views of course ressource in the `since` -> `until` date range."""
    # Switch/case pattern matching with the unique boolean tuple
    logger.debug("Start computing 'views' indicator")
    klass_mapping = {
        True: DailyUniqueViews,
        False: DailyViews,
    }
    indicator = klass_mapping.get(unique, DailyViews)(
        object_id=course_id,
        span_range=DatetimeRange.parse_obj(filters),
        activities=activities,
    )  # type: ignore[abstract]
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
