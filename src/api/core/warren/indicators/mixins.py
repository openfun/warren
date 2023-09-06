"""Mixins for indicators."""
import hashlib
from abc import ABC, abstractmethod
from functools import cached_property, reduce
from typing import Iterator, List, Literal, Union

from arrow import Arrow
from sqlmodel import Session, select

from warren.db import engine as db_engine

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


class CacheMixin:
    """A cache mixin that handles indicator persistence."""

    db_engine = db_engine

    @cached_property
    def db_session(self):
        """Get a database session."""
        with Session(self.db_engine) as session:
            return session

    @cached_property
    def cache_key(self) -> str:
        """Calculate the indicator cache key.

        The cache key is composed of the class name and an hexadecimal digest
        of the LRS query hash (excluding the since and until fields if present),
        e.g. fooindicator-44709d6fcb83d92a76dcb0b668c98e1b1d3dafe7.

        """
        lrs_query_hash = hashlib.sha256(
            self.get_lrs_query().json(exclude={"query": {"since", "until"}}).encode()
        ).hexdigest()
        return f"{self.__class__.__name__.lower()}-{lrs_query_hash}"

    async def get_cache(self) -> CacheEntry:
        """Get cached results matching the cache key from the database."""
        return self.db_session.exec(
            select(CacheEntry).where(CacheEntry.key == self.cache_key)
        ).one_or_none()

    async def save(self, caches: Union[CacheEntry, List[CacheEntry]]):
        """Save cache instance(s) to the database."""
        if not isinstance(caches, list):
            caches = [caches]
        for cache in caches:
            self.db_session.add(cache)
        self.db_session.commit()

    async def get_or_compute(self, update: bool = False):
        """Get cached result (if any) or compute the result.

        Nota bene: if computed, the result is stored in the database.

        """
        cache = await self.get_cache()

        # Return cached value
        if cache is not None and not update:
            return cache.value

        value = await self.compute()

        if cache is None:
            cache = CacheEntryCreate(key=self.cache_key, value=value)
            await self.save(CacheEntry.from_orm(cache))
        elif update:
            cache.value = value
            await self.save(cache)

        return cache.value


class IncrementalCacheMixin(CacheMixin, ABC):
    """A cache mixin for indicators relying on date ranges.

    Using this mixin requires to define a "frame" for the cache of the
    indicator. A value of "day" or "days" means that we will save a cache entry
    for each day in the lrs_query.since to lrs_query.until date span range.

    """

    frame: Frames

    @staticmethod
    @abstractmethod
    def merge(a: dict, b: dict):
        """Merging function for computed results."""

    async def get_cache(self) -> Iterator[CacheEntry]:
        """Get cached results matching the cache key and the indicator span range."""
        return self.db_session.exec(
            select(CacheEntry)
            .where(
                CacheEntry.key == self.cache_key,
                CacheEntry.since >= self.since,
                CacheEntry.until <= self.until,
            )
            .order_by(CacheEntry.since)
        ).all()

    async def _get_continuous_cache_for_time_span(
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
            for since, until in Arrow.span_range(self.frame, self.since, self.until)
        ]

        # Mutate dummy cache entries with DB cached ones
        sinces = [c.since for c in caches]
        for db_cache in await self.get_cache():
            caches[sinces.index(db_cache.since)] = db_cache

        return caches

    async def get_or_compute(self, update: bool = False):
        """Get cached result (if any) or compute the result.

        Nota bene: if computed, the result is stored in the database.

        """
        caches = await self._get_continuous_cache_for_time_span()
        to_save = []
        for cache in caches:
            if isinstance(cache, CacheEntry) and not update:
                continue
            cache.value = await self.compute(since=cache.since, until=cache.until)
            if isinstance(cache, CacheEntryCreate):
                to_save.append(CacheEntry.from_orm(cache))
            elif update:
                to_save.append(cache)
        await self.save(to_save)

        return reduce(self.merge, [cache.value for cache in caches])
