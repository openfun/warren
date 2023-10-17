"""Abstract class defining the interface for an indicator."""
import copy
import inspect
from abc import ABC, abstractmethod
from datetime import datetime
from functools import cached_property
from typing import List

from ralph.exceptions import BackendException

from warren.backends import lrs_client as async_lrs_client
from warren.exceptions import LrsClientException
from warren.filters import DatetimeRange
from warren.models import XAPI_STATEMENT, LRSStatementsQuery


class BaseIndicator(ABC):
    """Base class for an indicator.

    Define the signature of the methods that should be implemented
    for indicators.
    """

    def __init__(self, span_range: DatetimeRange = None, **kwargs):
        """Instantiate the base indicator.

        Args:
            span_range (DatetimeRange): date/time span range on which
            the indicator needs to be computed

            kwargs (dict): indicator-specific extra arguments that will
            be stored as indicator attributes.
        """
        super().__setattr__("span_range", span_range)
        for attr, value in kwargs.items():
            super().__setattr__(attr, value)

    def __setattr__(self, name, value):
        """Indicators are immutable, setattr is forbidden."""
        raise AttributeError(f"Can't set attribute '{name}'")

    def __delattr__(self, name):
        """Indicators are immutable, delattr is forbidden."""
        raise AttributeError(f"Can't delete attribute '{name}'")

    def _replace(self, deep=False, **kwargs):
        """Return an indicator copy with overridden kwargs.

        Args:
            deep (bool): if True perform a deep copy (defaults to shallow)
            kwargs (dict): additional arguments

        Disclaimer:
            As by default we perform a shallow copy of indicator attributes,
            you must be aware of consequencies when an indicator attribute is
            passed as reference: the original object passed as a reference may
            be modified in the original indicator instance AND its copy.
        """
        copy_ = copy.deepcopy if deep else copy.copy
        self_args = copy_(self.__dict__)
        other_args = {
            param.name: self_args[param.name]
            for param in inspect.signature(self.__init__).parameters.values()
            if param.name in self_args
        }
        other_args.update(kwargs)

        return self.__class__(**other_args)

    @property
    def since(self) -> datetime:
        """Shortcut to the indicator date/time span minimal value."""
        return self.span_range.since

    @property
    def until(self) -> datetime:
        """Shortcut to the indicator date/time span maximal value."""
        return self.span_range.until

    @cached_property
    def lrs_client(self):
        """Get AsyncLRSHTTP instance."""
        return async_lrs_client

    @abstractmethod
    def get_lrs_query(self) -> LRSStatementsQuery:
        """Get the LRS query for fetching statements."""

    async def fetch_statements(self) -> List[XAPI_STATEMENT]:
        """Execute the LRS query to obtain statements required for this indicator.

        If lrs_query is None, it defaults to self.get_lrs_query()
        """
        try:
            return [
                value
                async for value in self.lrs_client.read(
                    target=self.lrs_client.statements_endpoint,
                    query=self.get_lrs_query(),
                )
            ]
        except BackendException as exception:
            raise LrsClientException("Failed to fetch statements") from exception

    @abstractmethod
    async def compute(self):
        """Execute the LRS query, and perform operations to get the indicator value."""
