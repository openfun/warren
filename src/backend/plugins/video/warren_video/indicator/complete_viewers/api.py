"""Video viewers indicator : total count of viewers who completed the video."""

from fastapi import APIRouter, Depends, HTTPException
from ralph.backends.http.lrs import LRSQuery
from ralph.exceptions import BackendException
from ralph.models.xapi.concepts.verbs.scorm_profile import CompletedVerb
from starlette import status
from typing_extensions import Annotated  # python <3.9 compat
from warren.backends import lrs_client
from warren.fields import IRI
from warren.filters import BaseQueryFilters
from warren_video.metric.count import Count

router = APIRouter()


@router.get("/{video_id:path}/complete_viewers")
async def complete_viewers(
    video_id: IRI,
    filters: Annotated[BaseQueryFilters, Depends()],
) -> Count:
    """Video complete viewers endpoint."""
    query = {
        "verb": CompletedVerb().id,
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

    unique_complete_viewers = set()
    for statement in statements:
        unique_complete_viewers.add(statement["actor"]["account"]["name"])

    return Count(total=len(list(unique_complete_viewers)))
