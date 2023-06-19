"""Warren API v1 video router."""
import logging
from functools import partial
from typing import Any, get_type_hints

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from ralph.backends.http.lrs import LRSQuery
from ralph.exceptions import BackendException
from starlette import status
from typing_extensions import Annotated  # python <3.9 compat
from warren_video.indicator.indicator import VideoIndicator

from warren.backends import lrs_client
from warren.fields import IRI
from warren.filters import BaseQueryFilters

router = APIRouter()

logger = logging.getLogger(__name__)


def register_indicator(indicator: VideoIndicator):
    """Registers video indicators into the router."""
    return_type = get_type_hints(indicator.metric).get("return")

    if not issubclass(return_type, BaseModel):
        raise BackendException("invalid metric return type: expected a pydantic model")

    router.add_api_route(
        f"/{{video_id:path}}/{indicator.name}",
        partial(_indicator_endpoint, indicator),
        response_model=return_type,
    )


async def _indicator_endpoint(
    indicator: VideoIndicator,
    video_id: IRI,
    filters: Annotated[BaseQueryFilters, Depends()],
) -> Any:
    """Generic Video indicator endpoint."""
    query = {
        "verb": indicator.verb.id,
        "activity": video_id,
        "since": filters.since.isoformat(),
        "until": filters.until.isoformat(),
    }

    logger.info("Querying LRS for %s with query: %s", indicator.name, query)

    try:
        statements = lrs_client.read(
            target="/xAPI/statements", query=LRSQuery(query=query)
        )
    except BackendException as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="xAPI statements query failed",
        ) from error

    if indicator.filter_callback:
        statements = filter(indicator.filter_callback, statements)

    return indicator.metric(list(statements), filters)
