"""Mixins for indicators."""

import hashlib
import inspect
import json
import logging
from abc import ABC, abstractmethod
from functools import cached_property, reduce
from typing import Any, List, Literal, Optional, Protocol, Sequence, Union

import arrow
import pandas as pd
from pydantic.main import BaseModel
from ralph.backends.data.async_lrs import LRSStatementsQuery
from sqlmodel import Session, select

from warren.db import get_session as get_db_session
from warren.filters import DatetimeRange
from warren.indicators import BaseIndicator
from warren.models import DailyCount, DailyCounts, DailyUniqueCount, DailyUniqueCounts
from warren.utils import pipe
from warren.xapi import StatementsTransformer

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

        The cache key is composed of the class name and a hexadecimal digest of the
        instance attributes, e.g.
        fooindicator-44709d6fcb83d92a76dcb0b668c98e1b1d3dafe7.

        Note that instance attributes need to be serializable, or at least implement the
        __str__ method.

        """
        attributes = json.dumps(vars(self), sort_keys=True, default=str)
        attributes_hash = hashlib.sha256(attributes.encode()).hexdigest()
        return f"{self.__class__.__name__.lower()}-{attributes_hash}"

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
        if issubclass(self._compute_annotation, BaseModel):
            value = value.json()

        # Cache entry may have been created during a long compute time
        cache = await self.get_cache()

        if cache is None:
            cache = CacheEntry.parse_obj(
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

    @cached_property
    def cache_key(self) -> str:
        """Calculate the indicator cache key.

        The cache key is composed of the class name and a hexadecimal digest
        of the class instance attributes (excluding the span_range field if present),
        e.g. fooindicator-44709d6fcb83d92a76dcb0b668c98e1b1d3dafe7.

        """
        attr_copy = vars(self).copy()
        attr_copy.pop("span_range", None)
        attributes = json.dumps(attr_copy, sort_keys=True, default=str)
        attributes_hash = hashlib.sha256(attributes.encode()).hexdigest()
        return f"{self.__class__.__name__.lower()}-{attributes_hash}"

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


class BaseDailyEvent(BaseIndicator, IncrementalCacheMixin):
    """Base Daily Event indicator.

    This class defines a base daily event indicator. Given an event type, an object,
    and a date range, it calculates the total number of events and the number
    of events per day.

    Required: Indicators inheriting from this base class must declare a 'verb_id'
    class attribute with their xAPI verb ID.
    """

    frame: Frames = "day"
    verb_id: Optional[str] = None
    object_id: str

    def __init__(
        self,
        object_id: str,
        span_range: DatetimeRange,
    ):
        """Instantiate the Daily Event Indicator.

        Args:
            object_id: The ID of the ressource on which to compute the metric
            span_range: The date range on which to compute the indicator. It has
                2 fields, `since` and `until` which are dates or timestamps that must be
                in ISO format (YYYY-MM-DD, YYYY-MM-DDThh:mm:ss.sss±hh:mm or
                YYYY-MM-DDThh:mm:ss.sssZ")
        """
        super().__init__(span_range=span_range, object_id=object_id)

    def get_lrs_query(
        self,
    ) -> LRSStatementsQuery:
        """Get the LRS query for fetching required statements."""
        return LRSStatementsQuery(
            verb=self.verb_id,
            activity=self.object_id,
            since=self.since,
            until=self.until,
        )

    def filter_statements(self, statements: pd.DataFrame) -> pd.DataFrame:
        """Filter statements required for this indicator.

        This method may be overridden for indicator-specific filtering.
        """
        return statements

    def to_span_range_timezone(self, statements: pd.DataFrame) -> pd.DataFrame:
        """Convert 'timestamps' column to the DatetimeRange's timezone."""
        statements = statements.copy()
        statements["timestamp"] = statements["timestamp"].dt.tz_convert(
            self.span_range.tzinfo
        )
        return statements

    @staticmethod
    def extract_date_from_timestamp(statements: pd.DataFrame) -> pd.DataFrame:
        """Convert the 'timestamp' column to a 'date' column with its date values."""
        statements = statements.copy()
        statements["date"] = statements["timestamp"].dt.date
        statements.drop(["timestamp"], axis=1, inplace=True)
        return statements


class DailyEvent(BaseDailyEvent):
    """Daily Event indicator.

    Required: Indicators inheriting from this base class must declare a 'verb_id'
    class attribute with their xAPI verb ID.
    """

    def __init_subclass__(cls, **kwargs):
        """Ensure subclasses have a 'verb_id' class attribute."""
        super().__init_subclass__(**kwargs)
        if cls.verb_id is None:
            raise TypeError("Indicators must declare a 'verb_id' class attribute")

    async def compute(self) -> DailyCounts:
        """Fetch statements and computes the current indicator.

        Fetch the statements from the LRS, filter and aggregate them to return the
        number of activity events per day.
        """
        # Initialize daily counts within the specified date range,
        # with counts equal to zero
        daily_counts = DailyCounts.from_range(self.since, self.until)

        raw_statements = await self.fetch_statements()
        if not raw_statements:
            return daily_counts
        statements = pipe(
            StatementsTransformer.preprocess,
            self.filter_statements,
            self.to_span_range_timezone,
            self.extract_date_from_timestamp,
        )(raw_statements)

        # Compute daily counts from 'statements' DataFrame
        # and merge them into the 'daily_counts' object
        daily_counts.merge_counts(
            [
                DailyCount(date=date, count=count)
                for date, count in statements.groupby("date").size().items()
            ]
        )
        return daily_counts

    @staticmethod
    def merge(a: DailyCounts, b: DailyCounts) -> DailyCounts:
        """Merging function for computed indicators."""
        a.merge_counts(b.counts)
        return a


class DailyUniqueEvent(BaseDailyEvent):
    """Daily Unique Event indicator.

    This class defines a base unique daily event indicator. Given an event
    type, an activity, and a date range, it calculates the total number of unique
    user events and the number of unique user events per day.
    """

    def __init_subclass__(cls, **kwargs):
        """Ensure subclasses have a 'verb_id' class attribute."""
        super().__init_subclass__(**kwargs)
        if cls.verb_id is None:
            raise TypeError("Indicators must declare a 'verb_id' class attribute")

    def filter_statements(self, statements: pd.DataFrame) -> pd.DataFrame:
        """Filter statements required for this indicator.

        If necessary, this method removes any duplicate actors from the statements.
        This filtering step is typically done to ensure that each actor's
        contributions are counted only once.
        """
        return statements.drop_duplicates(subset="actor.uid")

    async def compute(self) -> DailyUniqueCounts:
        """Fetch statements and computes the current indicator.

        Fetch the statements from the LRS, filter and aggregate them to return the
        number of unique activity events per day.
        """
        # Initialize daily unique counts within the specified date range,
        # with counts equal to zero
        daily_unique_counts = DailyUniqueCounts.from_range(self.since, self.until)

        raw_statements = await self.fetch_statements()
        if not raw_statements:
            return daily_unique_counts

        statements = pipe(
            StatementsTransformer.preprocess,
            self.filter_statements,
            self.to_span_range_timezone,
            self.extract_date_from_timestamp,
        )(raw_statements)

        counts = []
        for date, users in statements.groupby("date")["actor.uid"].unique().items():
            counts.append(
                DailyUniqueCount(date=date, count=len(users), users=set(users))
            )
        daily_unique_counts.merge_counts(counts)

        return daily_unique_counts

    @staticmethod
    def merge(a: DailyUniqueCounts, b: DailyUniqueCounts) -> DailyUniqueCounts:
        """Merging function for computed indicators."""
        a.merge_counts(b.counts)
        return a
