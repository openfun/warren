"""API routes related to application health checking."""

import logging
from enum import Enum, unique

from fastapi import APIRouter, Response, status
from pydantic import BaseModel
from ralph.backends.http.base import HTTPBackendStatus

from warren.backends import lrs_client
from warren.db import is_alive as is_db_alive

logger = logging.getLogger(__name__)

router = APIRouter()


@unique
class BackendStatus(str, Enum):
    """Generic backend statuses inspired from Ralph HTTP backend."""

    OK = "ok"
    AWAY = "away"
    ERROR = "error"


class Heartbeat(BaseModel):
    """Warren backends status."""

    database: BackendStatus
    lrs: HTTPBackendStatus

    @property
    def is_alive(self):
        """A helper that checks the overall status."""
        if self.database == BackendStatus.OK and self.lrs == HTTPBackendStatus.OK:
            return True
        return False


@router.get("/__lbheartbeat__")
async def lbheartbeat() -> None:
    """Load balancer heartbeat.

    Return a 200 when the server is running.
    """
    return


@router.get("/__heartbeat__", status_code=status.HTTP_200_OK)
async def heartbeat(response: Response) -> Heartbeat:
    """Application heartbeat.

    Return a 200 if all checks are successful.
    """
    statuses = Heartbeat(
        database=BackendStatus.OK if is_db_alive() else BackendStatus.ERROR,
        lrs=await lrs_client.status(),
    )
    if not statuses.is_alive:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    return statuses
