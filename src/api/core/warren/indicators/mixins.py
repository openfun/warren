"""Mixins for indicators."""
import hashlib
import inspect
import logging
from abc import ABC, abstractmethod
from functools import cached_property, reduce
from typing import Any, List, Literal, Protocol, Sequence, Union

import arrow
from pydantic.main import BaseModel
from sqlmodel import Session, select

from warren.db import get_session as get_db_session
from warren.filters import DatetimeRange

from .models import CacheEntry, CacheEntryCreate

# Inspired from Arrow's _T_FRAMES
Frames = Literal[
    "year",
    "years",
    "month",
    "months",
    "day",
    "days",
    "hour",
    "hours",
    "minute",
    "minutes",
    "second",
    "seconds",
    "microsecond",
    "microseconds",
    "week",
    "weeks",
    "quarter",
    "quarters",
]

logger = logging.getLogger(__name__)


class Cacheable(Protocol):
    """A protocol defining the structure for cacheable objects."""

    def get_lrs_query(self):
        """Get the LRS query for fetching statements."""
        ...

    async def compute(self):
        """Perform operations to get a computed value."""
        ...


class CacheMixin(Cacheable):
    """A cache mixin that handles indicator persistence."""

    @property
    def db_session(self) -> Session:
        """Get the database session singleton."""
        session = get_db_session()
        logger.debug("Indicator session: %s", session.__dict__)
        return session

    @cached_property
    def cache_key(self) -> str:
        """Calculate the indicator cache key.

        The cache key is composed of the class name and a hexadecimal digest
        of the LRS query hash (excluding the since and until fields if present),
        e.g. fooindicator-44709d6fcb83d92a76dcb0b668c98e1b1d3dafe7.

        """
        lrs_query_hash = hashlib.sha256(
            self.get_lrs_query()
            .json(exclude={"since", "until"}, exclude_none=True, exclude_unset=True)
            .encode()
        ).hexdigest()
        return f"{self.__class__.__name__.lower()}-{lrs_query_hash}"

    async def get_cache(self) -> Union[CacheEntry, None]:
        """Get cached results matching the cache key from the database."""
        return self.db_session.exec(
            select(CacheEntry).where(CacheEntry.key == self.cache_key)
        ).one_or_none()

    async def save(self, caches: Union[CacheEntry, List[CacheEntry]]):
        """Save cache instance(s) to the database."""
        if not isinstance(caches, list):
            caches = [caches]
        with self.db_session.begin_nested():
            for cache in caches:
                self.db_session.add(cache)
        self.db_session.commit()

    @cached_property
    def _compute_annotation(self):
        """Get the annotation type returned by the compute method.

        Raises:
            TypeError if no type annotation is defined for the compute method.
        """
        annotation = inspect.signature(self.compute).return_annotation
        if annotation == inspect.Signature.empty:
            raise TypeError(
                "compute method of an indicator should declare a return annotation"
            )
        return annotation

    @staticmethod
    def _to_pydantic(model: BaseModel, value: Any):
        """Deserialize values to the given Pydantic model."""
        return (
            model.parse_raw(value) if isinstance(value, str) else model.parse_obj(value)
        )

    def _raw_or_pydantic(self, value: Any):
        """Return raw value or pydantic model instance."""
        return (
            self._to_pydantic(self._compute_annotation, value)
            if issubclass(self._compute_annotation, BaseModel)
            else value
        )

    async def get_or_compute(self, update: bool = False):
        """Get cached result (if any) or compute the result.

        Nota bene: if computed, the result is stored in the database.

        """
        cache = await self.get_cache()

        # Return cached value
        if cache is not None and not update:
            return self._raw_or_pydantic(cache.value)

        value = await self.compute()

        if cache is None:
            cache = CacheEntry.model_validate(
                CacheEntryCreate(key=self.cache_key, value=value)
            )
            await self.save(cache)
        elif update:
            cache.value = value
            await self.save(cache)

        return self._raw_or_pydantic(cache.value)


class CacheableIncrementally(Cacheable):
    """Protocol for cacheable object with incremental capabilities."""

    @property
    def since(self):
        """Shortcut to the object date/time span minimal value."""
        ...

    @property
    def until(self):
        """Shortcut to the object date/time span minimal value."""
        ...

    def _replace(self, deep=False, **kwargs):
        """Return an object copy with overridden kwargs."""
        ...


class IncrementalCacheMixin(CacheMixin, CacheableIncrementally, ABC):
    """A cache mixin for indicators relying on date ranges.

    Using this mixin requires to define a "frame" for the cache of the
    indicator. A value of "day" or "days" means that we will save a cache entry
    for each day in the lrs_query.since to lrs_query.until date span range.

    """

    frame: Frames

    @staticmethod
    @abstractmethod
    def merge(a: Any, b: Any) -> Any:
        """Merging function for computed results."""

    async def get_caches(self) -> Sequence[CacheEntry]:
        """Get cached results matching the cache key and the indicator span range."""
        return self.db_session.exec(
            select(CacheEntry)
            .where(
                CacheEntry.key == self.cache_key,
                CacheEntry.since >= self.since,  # type: ignore[operator]
                CacheEntry.until <= arrow.get(self.until).ceil(self.frame).datetime,  # type: ignore[operator]
            )
            .order_by(CacheEntry.since)  # type: ignore[arg-type]
        ).all()

    async def _get_continuous_caches_for_time_span(
        self,
    ) -> List[Union[CacheEntry, CacheEntryCreate]]:
        """Generates a list mixing dummy cache and real DB cache."""
        # Prepare dummy cache list
        caches = [
            CacheEntryCreate.construct(
                key=self.cache_key,
                since=since.datetime,
                until=until.datetime,
                value=None,
            )
            for since, until in arrow.Arrow.span_range(
                self.frame, self.since, self.until
            )
        ]

        # Mutate dummy cache entries with DB cached ones
        sinces = [c.since for c in caches]
        for db_cache in await self.get_caches():
            caches[sinces.index(db_cache.since)] = db_cache

        return caches

    async def get_or_compute(self, update: bool = False):
        """Get cached result (if any) or compute the result.

        Nota bene: if computed, the result is stored in the database.

        """
        caches = await self._get_continuous_caches_for_time_span()
        to_save = []
        to_update = []
        for cache in caches:
            if isinstance(cache, CacheEntry) and not update:
                logger.debug("Cache entry with ID %s wont be updated", str(cache.id))
                continue
            # Get a new indicator instance for a reduced date/time span range
            other = self._replace(
                span_range=DatetimeRange(since=cache.since, until=cache.until)
            )
            result = await other.compute()

            # Pydantic case
            if isinstance(result, BaseModel):
                result = result.json()

            cache.value = result
            if isinstance(cache, CacheEntry):
                to_update.append(cache)
            elif isinstance(cache, CacheEntryCreate):
                to_save.append(CacheEntry.model_validate(cache))

        await self.save(to_update)
        await self.save(to_save)

        values = [self._raw_or_pydantic(cache.value) for cache in caches]

        return reduce(self.merge, values)
