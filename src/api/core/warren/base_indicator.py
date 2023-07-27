"""Abstract class defining the interface for an indicator."""
import hashlib
from abc import ABC, abstractmethod
from typing import List

import pandas as pd
from ralph.backends.http.async_lrs import LRSQuery

from warren.conf import settings


def parse_raw_statements(raw_statements) -> pd.DataFrame:
    """Parse LRS statements, explode the columns, and add a `date` column."""
    flattened = pd.json_normalize(raw_statements)
    # Disable chained assignment warning to make the transformation inplace
    pd.options.mode.chained_assignment = None
    # Transform timestamp column into a date with day (YYYY-MM-DD)
    flattened.loc[:, "date"] = pd.to_datetime(flattened.loc[:, "timestamp"]).dt.date
    return flattened


def add_actor_uid(statements: pd.DataFrame) -> pd.DataFrame:
    """Add a `actor.uid` column that uniquely identifies the agent.

    Depending on the xAPI statements, the actor can be identified in 4 different ways :
    https://github.com/adlnet/xAPI-Spec/blob/master/xAPI-Data.md#details-4. This
    function handles the 4 cases and creates a `uid` column that can be used later
    without worrying about the 4 IFIs.
    """
    xapi_actor_identifier_columns = settings.XAPI_ACTOR_IDENTIFIER_PATHS.intersection(
        set(statements.columns)
    )

    if len(xapi_actor_identifier_columns) == 0:
        raise ValueError(
            "There is no way of identifying the agent in submitted statements."
        )
    statements["actor.uid"] = statements.apply(
        lambda row: hashlib.sha256(
            "-".join(str(row[col]) for col in xapi_actor_identifier_columns).encode()
        ).hexdigest(),
        axis=1,
    )

    return statements


def pre_process_statements(statements: List) -> pd.DataFrame:
    """Denormalize raw statements, and add utility columns."""
    parsed = parse_raw_statements(statements)
    with_actor_uid = add_actor_uid(parsed)
    return with_actor_uid


class BaseIndicator(ABC):
    """Base class for an indicator.

    Defines the signature of the methods that should be implemented
    for indicators.
    """

    @abstractmethod
    def get_lrs_query(self) -> LRSQuery:
        """Gets the LRS query for fetching statements."""

    @abstractmethod
    async def fetch_statements(self) -> List:
        """Executes the LRS query to obtain statements required for the indicator."""

    @abstractmethod
    async def compute(self):
        """Executes the LRS query, and perform operations to get the indicator value."""
