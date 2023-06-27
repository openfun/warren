"""Abstract class defining the interface for an indicator."""
from abc import ABC, abstractmethod
from typing import List

from ralph.backends.http.lrs import LRSQuery


class BaseIndicator(ABC):
    """Base class for an indicator.

    Defines the signature of the methods that should be implemented
    for indicators. Indicators should implement this interface.
    """

    @abstractmethod
    def get_lrs_query(self) -> LRSQuery:
        """Gets the LRS query for fetching statements."""

    @abstractmethod
    def fetch_statements(self) -> List:
        """Executes the LRS query to obtain statements required for the indicator."""

    @abstractmethod
    def compute(self):
        """Executes the query, and perform operations to get the indicator value."""
