"""Downloads indicator : day time series of the video downloads."""

from fastapi import APIRouter, Depends, HTTPException
from ralph.backends.http.lrs import LRSQuery
from ralph.exceptions import BackendException
from ralph.models.xapi.concepts.verbs.tincan_vocabulary import DownloadedVerb
from starlette import status
from typing_extensions import Annotated  # python <3.9 compat
from warren_video.metric.daytimeseries import DayTimeSeries, create_day_time_series

from warren.backends import lrs_client
from warren.fields import IRI
from warren.filters import BaseQueryFilters

router = APIRouter()


@router.get("/{video_id:path}/downloads")
async def downloads(
    video_id: IRI,
    filters: Annotated[BaseQueryFilters, Depends()],
) -> DayTimeSeries:
    """Video downloads endpoint."""
    query = {
        "verb": DownloadedVerb().id,
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

    return create_day_time_series(list(statements), filters)
