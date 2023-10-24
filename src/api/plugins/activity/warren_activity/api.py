"""Warren API v1 activity router."""

import logging

from fastapi import APIRouter, Depends, HTTPException
from typing_extensions import Annotated  # python <3.9 compat
from warren.exceptions import LrsClientException
from warren.fields import IRI
from warren.filters import BaseQueryFilters, DatetimeRange
from warren.models import DailyCounts
from .indicators import CohortDailyActivity, StudentDailyActivity

router = APIRouter(
    prefix="/activity"
)

logger = logging.getLogger(__name__)

@router.get("{activity-id}/student/{student-id}")
async def student_activity(
    student_ifi: str,
    activity_id: IRI,
    filters: Annotated[BaseQueryFilters, Depends()],
    unique: bool = False,
) -> DailyCounts: 
    """Number of actions the student has made in a given activity."""

    indicator = StudentDailyActivity(
        student_ifi=student_ifi,
        activity_id=activity_id,
        date_range=DatetimeRange.parse_obj(filters),
        unique=unique,
    )

    try:
        return await indicator.compute()
    except (KeyError, AttributeError, LrsClientException) as exception:
        message = "An error occurred while computing the student activity"
        logger.error("%s: %s", message, exception)
        raise HTTPException(status_code=500, detail=message) from exception
    
@router.get("{activity-id}/cohort")
async def cohort_activity(
    activity_id: IRI,
    filters: Annotated[BaseQueryFilters, Depends()],
    unique: bool = False,
) -> DailyCounts: 
    """Average number of actions a cohort has made in a given activity."""

    indicator = CohortDailyActivity(
        activity_id=activity_id,
        date_range=DatetimeRange.parse_obj(filters),
        unique=unique,
    )

    try:
        return await indicator.compute()
    except (KeyError, AttributeError, LrsClientException) as exception:
        message = "An error occurred while computing the cohort activity"
        logger.error("%s: %s", message, exception)
        raise HTTPException(status_code=500, detail=message) from exception
    
# TODO Add an indicator for position on the cohort