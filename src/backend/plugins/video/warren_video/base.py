from abc import ABC, abstractmethod
from typing import List
from ralph.backends.http.lrs import BaseHTTP, LRSQuery


class BaseIndicator(ABC):
    client: BaseHTTP

    @abstractmethod
    def __init__(self):
        pass

    @abstractmethod
    def get_query(self) -> LRSQuery:
        """
        Returns the query that will be issued to the `client` to get the statements required to compute this indicator
        """
        pass

    @abstractmethod
    def get_statements(self) -> List:
        """
        Executes the query to get the statements required to compute this indicator
        """
        pass

    @abstractmethod
    def compute(self):
        """
        Executes the query, and perform relevant operations (sum, aggregations...) to get the final indicator value
        """
        pass
