"""Experience Index ETL Protocol and Mixin for indexers."""


from typing import Iterator, List, Protocol, TypeVar


class Executable(Protocol):
    """Protocol representing an executable entity."""

    async def execute(self):
        """Execute the operation asynchronously."""
        ...


Source = TypeVar("Source")
Destination = TypeVar("Destination")


class ETL(Protocol[Source, Destination]):
    """Protocol for a data engineering ETL (Extract, Transform, Load) process."""

    @classmethod
    async def factory(cls, *args, **kwargs):
        """Create an instance of the ETL class."""
        ...

    async def _extract(self, *args, **kwargs) -> List[Source]:
        """Extract data from the source."""
        ...

    def _transform(self, raw: List[Source], *args, **kwargs) -> Iterator[Destination]:
        """Transform extracted data."""
        ...

    async def _load(self, data: Iterator[Destination], *args, **kwargs):
        """Load transformed data to the destination."""
        ...


class ETLRunnerMixin(Executable):
    """Mixin for executing an ETL (Extract, Transform, Load) process."""

    async def execute(self):
        """Execute the ETL process.

        Orchestrates the execution of the ETL process by:
        1. Extracting raw data using _extract method.
        2. Transforming the extracted data using _transform method.
        3. Loading the transformed data using _load method.

        """
        raw = await self._extract()
        data = self._transform(raw)

        await self._load(data)
