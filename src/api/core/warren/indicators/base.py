"""Abstract class defining the interface for an indicator."""
from abc import ABC, abstractmethod
from functools import cached_property
from typing import List

from ralph.exceptions import BackendException

from warren.backends import lrs_client as async_lrs_client
from warren.exceptions import LrsClientException
from warren.models import XAPI_STATEMENT, LRSStatementsQuery


class BaseIndicator(ABC):
    """Base class for an indicator.

    Define the signature of the methods that should be implemented
    for indicators.
    """

    @cached_property
    def lrs_client(self):
        """Get AsyncLRSHTTP instance."""
        return async_lrs_client

    @abstractmethod
    def get_lrs_query(self) -> LRSStatementsQuery:
        """Get the LRS query for fetching statements."""

    async def fetch_statements(
        self, lrs_query: LRSStatementsQuery = None
    ) -> List[XAPI_STATEMENT]:
        """Execute the LRS query to obtain statements required for this indicator.

        If lrs_query is None, it defaults to self.get_lrs_query()
        """
        try:
            return [
                value
                async for value in self.lrs_client.read(
                    target=self.lrs_client.statements_endpoint,
                    query=lrs_query or self.get_lrs_query(),
                )
            ]
        except BackendException as exception:
            raise LrsClientException("Failed to fetch statements") from exception

    @abstractmethod
    async def compute(self):
        """Execute the LRS query, and perform operations to get the indicator value."""
