"""Experience Index API filters."""

from fastapi import Query
from pydantic import BaseModel


class Pagination(BaseModel):
    """Common query filters used for pagination."""

    offset: int = Query(default=0, ge=0, description="The number of items to offset")
    limit: int = Query(
        default=100, le=100, description="The maximum number of items to retrieve"
    )
