"""Count metric for counting statements."""

from typing import Dict, List

from pydantic import BaseModel

from warren.filters import BaseQueryFilters


class Count(BaseModel):
    """A simple count literal metric."""

    total: int


def count_metric(statements: List[Dict], _: BaseQueryFilters) -> Count:
    """Simply count the number of statements. Follows the METRIC type signature."""
    return Count(total=len(statements))
