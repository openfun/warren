"""Abstract class defining the interface for an indicator."""
from abc import ABC, abstractmethod
from typing import List

import pandas as pd
from ralph.backends.http.lrs import LRSQuery


def parse_raw_statements(raw_statements):
    """Parse LRS statements, explode the columns, and add a `date` column."""
    flattened = pd.json_normalize(raw_statements)
    # Disable chained assignment warning to make the transformation inplace
    pd.options.mode.chained_assignment = None
    flattened.loc[:, "timestamp"] = pd.to_datetime(flattened.loc[:, "timestamp"])
    # Create a date column in the YYYY-MM-DD format
    flattened.loc[:, "date"] = flattened.loc[:, "timestamp"].dt.date
    return flattened


class BaseIndicator(ABC):
    """Base class for an indicator.

    Defines the signature of the methods that should be implemented
    for indicators.
    """

    @abstractmethod
    def get_lrs_query(self) -> LRSQuery:
        """Gets the LRS query for fetching statements."""

    @abstractmethod
    def fetch_statements(self) -> List:
        """Executes the LRS query to obtain statements required for the indicator."""

    @abstractmethod
    def compute(self):
        """Executes the LRS query, and perform operations to get the indicator value."""
