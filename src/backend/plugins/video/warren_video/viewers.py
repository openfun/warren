"""Video viewers indicator : total count of viewers who played the video."""

from fastapi import APIRouter, Depends, HTTPException
from ralph.backends.http.lrs import LRSQuery
from ralph.exceptions import BackendException
from ralph.models.xapi.concepts.verbs.scorm_profile import CompletedVerb
from ralph.models.xapi.concepts.verbs.video import PlayedVerb
from starlette import status
from typing_extensions import Annotated  # python <3.9 compat
from warren.backends import lrs_client
from warren.fields import IRI
from warren.filters import BaseQueryFilters
from warren_video.metric.count import Count
from warren_video.statement_filters import filter_played_views

router = APIRouter()


@router.get("/{video_id:path}/viewers")
async def viewers(
    video_id: IRI,
    filters: Annotated[BaseQueryFilters, Depends()],
    completed: bool = False,
) -> Count:
    """Video viewers endpoint."""
    verb = CompletedVerb() if completed else PlayedVerb()

    query = {
        "verb": verb.id,
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

    if verb == PlayedVerb():
        statements = filter(filter_played_views, statements)

    unique_viewers = {statement["actor"]["account"]["name"] for statement in statements}

    return Count(total=len(unique_viewers))
