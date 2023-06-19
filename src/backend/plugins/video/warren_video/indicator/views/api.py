"""Views indicator : day time series of the video views."""

from fastapi import APIRouter, Depends, HTTPException
from ralph.backends.http.lrs import LRSQuery
from ralph.exceptions import BackendException
from ralph.models.xapi.concepts.verbs.video import PlayedVerb
from starlette import status
from typing_extensions import Annotated  # python <3.9 compat
from warren.backends import lrs_client
from warren.fields import IRI
from warren.filters import BaseQueryFilters
from warren_video.metric.daytimeseries import DayTimeSeries, create_day_time_series
from warren_video.statement_filters import filter_played_views

router = APIRouter()


@router.get("/{video_id:path}/views")
async def views(
    video_id: IRI,
    filters: Annotated[BaseQueryFilters, Depends()],
) -> DayTimeSeries:
    """Video views endpoint."""
    query = {
        "verb": PlayedVerb().id,
        "activity": video_id,
        "since": filters.since.isoformat(),
        "until": filters.until.isoformat(),
    }

    try:
        statements = lrs_client.read(
            target="/xAPI/statements", query=LRSQuery(query=query)
        )
    except BackendException as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="xAPI statements query failed",
        ) from error

    statements = filter(filter_played_views, statements)

    return create_day_time_series(list(statements), filters)
