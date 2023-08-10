"""Abstract class defining the interface for an indicator."""
import hashlib
from abc import ABC, abstractmethod
from typing import List

import pandas as pd
from ralph.backends.http.async_lrs import LRSQuery

from warren.conf import settings
from warren.models import XAPI_STATEMENT


class PreprocessMixin(object):
    """Mixin class for preprocessing xAPI statements.

    This class provides methods to parse LRS statements, add a 'date' column,
    and add an 'actor.uid' column that uniquely identifies the agent.
    It also includes a method to preprocess the statements and apply all
    the necessary transformations all at once.
    """

    raw_statements: List[XAPI_STATEMENT] = None
    statements: pd.DataFrame = None

    def parse_raw_statements(self) -> None:
        """Parse LRS statements, explode the columns."""
        self.statements = pd.json_normalize(self.raw_statements)

    def add_date_column(self) -> None:
        """Add a 'date' column computed from statement's timestamp."""
        # Disable chained assignment warning to make the transformation inplace
        with pd.option_context("mode.chained_assignment", None):
            # Transform 'timestamp' column into a date with the format (YYYY-MM-DD)
            self.statements["date"] = pd.to_datetime(
                self.statements["timestamp"]
            ).dt.date

    def add_actor_uid_column(self) -> None:
        """Add a 'actor.uid' column that uniquely identifies the agent.

        Depending on the xAPI statements, the actor can be identified in 4 ways:
        https://github.com/adlnet/xAPI-Spec/blob/master/xAPI-Data.md#details-4. This
        function handles the 4 cases and creates a `uid` column that can be used later
        without worrying about the 4 IFIs.
        """
        xapi_actor_identifier_columns = (
            settings.XAPI_ACTOR_IDENTIFIER_PATHS.intersection(
                set(self.statements.columns)
            )
        )

        if not xapi_actor_identifier_columns:
            raise ValueError(
                "There is no way of identifying the agent in submitted statements."
            )

        def get_uid(row):
            return hashlib.sha256(
                "-".join(
                    str(row[col]) for col in xapi_actor_identifier_columns
                ).encode()
            ).hexdigest()

        self.statements["actor.uid"] = self.statements.apply(get_uid, axis=1)

    def preprocess_statements(self) -> None:
        """Denormalize raw statements, and add utility columns."""
        self.parse_raw_statements()
        self.add_actor_uid_column()
        self.add_date_column()


class BaseIndicator(ABC):
    """Base class for an indicator.

    Define the signature of the methods that should be implemented
    for indicators.
    """

    @abstractmethod
    def get_lrs_query(self) -> LRSQuery:
        """Get the LRS query for fetching statements."""

    @abstractmethod
    async def fetch_statements(self) -> None:
        """Execute the LRS query to obtain statements required for the indicator."""

    @abstractmethod
    def filter_statements(self) -> None:
        """Filter the statements required for the indicator."""

    @abstractmethod
    async def compute(self):
        """Execute the LRS query, and perform operations to get the indicator value."""

    @abstractmethod
    async def persist(self):
        """Save the computed indicator value in the configured database."""
