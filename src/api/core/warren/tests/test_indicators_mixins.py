"""Test indicators mixins."""
import hashlib
from datetime import datetime, timezone
from itertools import chain
from typing import Union
from unittest.mock import AsyncMock

import pytest
from arrow import Arrow
from freezegun import freeze_time
from ralph.backends.http.async_lrs import LRSQuery
from sqlalchemy.exc import MultipleResultsFound
from sqlmodel import select

from warren.filters import DatetimeRange
from warren.indicators.base import BaseIndicator
from warren.indicators.mixins import CacheMixin, IncrementalCacheMixin
from warren.indicators.models import CacheEntry


def test_cache_key_calculation():
    """Test the cache key calculation."""

    class MyIndicator(CacheMixin, BaseIndicator):
        """Dummy indicator."""

        def get_lrs_query(self) -> LRSQuery:
            return LRSQuery(query={"verb": "played"})

        async def fetch_statements(self):
            pass

        async def compute(self):
            pass

    indicator = MyIndicator()
    lrs_query = '{"query_string": null, "query": {"verb": "played"}}'
    expected = f"myindicator-{hashlib.sha256(lrs_query.encode()).hexdigest()}"
    assert indicator.cache_key == expected


def test_cache_key_calculation_with_lrs_query_datetime_range():
    """Test the cache key calculation when the LRS query as date time range
    (since/until) parameters set.

    """  # noqa: D205

    class MyIndicator(CacheMixin, BaseIndicator):
        """Dummy indicator."""

        def get_lrs_query(self) -> LRSQuery:
            return LRSQuery(
                query={
                    "verb": "played",
                    "since": datetime(2023, 1, 1),
                    "until": datetime(2023, 2, 1),
                }
            )

        async def fetch_statements(self):
            pass

        async def compute(self):
            pass

    indicator = MyIndicator()
    # We exclude "since" and "until" parameters from the LRS query to calculate
    # the cache key
    lrs_query = '{"query_string": null, "query": {"verb": "played"}}'
    expected = f"myindicator-{hashlib.sha256(lrs_query.encode()).hexdigest()}"
    assert indicator.cache_key == expected


@pytest.mark.anyio
@freeze_time("2023-10-14")
async def test_save_with_single_cache_instance(db_session):
    """Test saving cached results to the database."""

    class MyIndicator(CacheMixin, BaseIndicator):
        """Dummy indicator."""

        def get_lrs_query(self) -> LRSQuery:
            return LRSQuery(query={"verb": "played"})

        async def fetch_statements(self):
            pass

        async def compute(self):
            pass

    indicator = MyIndicator()
    caches = db_session.exec(
        select(CacheEntry).where(CacheEntry.key == indicator.cache_key)
    ).all()
    assert len(caches) == 0
    await indicator.save(CacheEntry(key=indicator.cache_key, value={"lol": [1, 2, 3]}))

    saved = db_session.exec(
        select(CacheEntry).where(CacheEntry.key == indicator.cache_key)
    ).one()

    assert isinstance(saved, CacheEntry)
    assert saved.key == indicator.cache_key
    assert saved.value == {"lol": [1, 2, 3]}
    assert saved.since is None
    assert saved.until is None
    assert saved.created_at == datetime(2023, 10, 14, tzinfo=timezone.utc)


@pytest.mark.anyio
async def test_save_with_multiple_cache_instances(db_session):
    """Test saving cached results to the database (multiple values case)."""

    class MyIndicator(CacheMixin, BaseIndicator):
        """Dummy indicator."""

        def get_lrs_query(self) -> LRSQuery:
            return LRSQuery(query={"verb": "played"})

        async def fetch_statements(self):
            pass

        async def compute(self):
            pass

    indicator = MyIndicator()
    caches = db_session.exec(
        select(CacheEntry).where(CacheEntry.key == indicator.cache_key)
    ).all()
    assert len(caches) == 0
    await indicator.save(
        [
            CacheEntry(key=indicator.cache_key, value={"bar": [1, 2, 3]}),
            CacheEntry(key=indicator.cache_key, value={"bar": [4, 5, 6]}),
        ]
    )

    saved = db_session.exec(
        select(CacheEntry)
        .where(CacheEntry.key == indicator.cache_key)
        .order_by("created_at")
    ).all()

    assert isinstance(saved, list)
    assert saved[0].key == indicator.cache_key
    assert saved[0].value == {"bar": [1, 2, 3]}
    assert saved[0].since is None
    assert saved[0].until is None
    assert saved[1].key == indicator.cache_key
    assert saved[1].value == {"bar": [4, 5, 6]}
    assert saved[1].since is None
    assert saved[1].until is None


@pytest.mark.anyio
async def test_get_cache(db_session):
    """Test getting cached results from the database."""

    class MyIndicatorA(CacheMixin, BaseIndicator):
        """Dummy indicator."""

        def get_lrs_query(self) -> LRSQuery:
            return LRSQuery(query={"verb": "played"})

        async def fetch_statements(self):
            pass

        async def compute(self):
            pass

    class MyIndicatorB(CacheMixin, BaseIndicator):
        """Dummy indicator."""

        def get_lrs_query(self) -> LRSQuery:
            return LRSQuery(query={"verb": "played"})

        async def fetch_statements(self):
            pass

        async def compute(self):
            pass

    a = MyIndicatorA()
    b = MyIndicatorB()

    db_session.add(CacheEntry(key=a.cache_key, value={"foo": [1, 2, 3]}))
    db_session.add(CacheEntry(key=b.cache_key, value={"foo": [4, 5, 6]}))
    db_session.commit()

    a_cache = await a.get_cache()
    assert a_cache.key == a.cache_key
    assert a_cache.value == {"foo": [1, 2, 3]}
    b_cache = await b.get_cache()
    assert b_cache.key == b.cache_key
    assert b_cache.value == {"foo": [4, 5, 6]}


@pytest.mark.anyio
async def test_get_cache_when_no_cache_exists(db_session):
    """Test getting cached results from the database when none has been saved yet."""

    class MyIndicator(CacheMixin, BaseIndicator):
        """Dummy indicator."""

        def get_lrs_query(self) -> LRSQuery:
            return LRSQuery(query={"verb": "played"})

        async def fetch_statements(self):
            pass

        async def compute(self):
            pass

    indicator = MyIndicator()

    caches = db_session.exec(
        select(CacheEntry).where(CacheEntry.key == indicator.cache_key)
    ).all()
    assert len(caches) == 0
    assert await indicator.get_cache() is None


@pytest.mark.anyio
async def test_get_cache_when_unexpected_multiple_cache_exist(db_session):
    """Test getting cached results from the database when multiple entries exist."""

    class MyIndicator(CacheMixin, BaseIndicator):
        """Dummy indicator."""

        def get_lrs_query(self) -> LRSQuery:
            return LRSQuery(query={"verb": "played"})

        async def fetch_statements(self):
            pass

        async def compute(self):
            pass

    indicator = MyIndicator()

    db_session.add(CacheEntry(key=indicator.cache_key, value={"foo": [1, 2, 3]}))
    db_session.add(CacheEntry(key=indicator.cache_key, value={"foo": [4, 5, 6]}))
    db_session.commit()

    with pytest.raises(
        MultipleResultsFound,
        match="Multiple rows were found when one or none was required",
    ):
        await indicator.get_cache()


@pytest.mark.anyio
async def test_get_or_compute(db_session):
    """Test getting cached results from the database or compute them."""

    class MyIndicator(CacheMixin, BaseIndicator):
        """Dummy indicator."""

        def get_lrs_query(self) -> LRSQuery:
            return LRSQuery(query={"verb": "played"})

        async def fetch_statements(self):
            pass

        async def compute(self):
            return {"foo": [1, 2, 3]}

    indicator = MyIndicator()

    # Check that nothing already exists in the database
    caches = db_session.exec(
        select(CacheEntry).where(CacheEntry.key == indicator.cache_key)
    ).all()
    assert len(caches) == 0

    result = await indicator.get_or_compute()
    # Check that result is ok and that we stored it in database
    assert result == {"foo": [1, 2, 3]}
    cached = db_session.exec(
        select(CacheEntry).where(CacheEntry.key == indicator.cache_key)
    ).all()
    assert len(cached) == 1
    assert cached[0].value == {"foo": [1, 2, 3]}

    # Mock the compute method so that we can spy on it and change the result
    indicator.compute = AsyncMock(return_value={"foo": [4, 5, 6]})

    # Call compute once again and ensure we don't recalculate the results
    result = await indicator.get_or_compute()
    assert result == {"foo": [1, 2, 3]}
    indicator.compute.assert_not_called()

    # Ok, now force the update
    result = await indicator.get_or_compute(update=True)
    assert result == {"foo": [4, 5, 6]}
    indicator.compute.assert_called_once()
    cached = db_session.exec(
        select(CacheEntry).where(CacheEntry.key == indicator.cache_key)
    ).all()
    assert len(cached) == 1
    assert cached[0].value == {"foo": [4, 5, 6]}


@pytest.mark.anyio
async def test_incremental_get_cache(db_session):
    """Test getting cache(s) for the incremental mixin."""

    class MyDailyIndicator(IncrementalCacheMixin, BaseIndicator):
        """Dummy indicator."""

        frame = "day"

        def get_lrs_query(
            self, since: datetime = None, until: datetime = None
        ) -> LRSQuery:
            return LRSQuery(query={"verb": "played", "since": since, "until": until})

        async def fetch_statements(self):
            pass

        async def compute(self, since: datetime = None, until: datetime = None):
            return {
                "day": since.day,
                "lrs_query": self.get_lrs_query(since=since, until=until).json(),
            }

        @staticmethod
        def merge(a: dict, b: dict):
            return (a, b)

    indicator = MyDailyIndicator(
        span_range=DatetimeRange(
            since=datetime(2023, 1, 1), until=datetime(2023, 1, 31)
        )
    )
    # Check that nothing already exists in the database
    caches = db_session.exec(
        select(CacheEntry).where(CacheEntry.key == indicator.cache_key)
    ).all()
    assert len(caches) == 0
    caches = await indicator.get_cache()
    assert len(caches) == 0

    # Create a cache entry and check we can get it back
    for since, until in chain(
        Arrow.span_range("day", Arrow(2023, 1, 10), Arrow(2023, 1, 15)),
        Arrow.span_range("day", Arrow(2023, 1, 18), Arrow(2023, 1, 21)),
    ):
        db_session.add(
            CacheEntry(
                key=indicator.cache_key,
                value={
                    "day": since.day,
                    "lrs_query": indicator.get_lrs_query(
                        since=since.datetime, until=until.datetime
                    ).json(),
                },
                since=since.datetime,
                until=until.datetime,
            )
        )
    db_session.commit()
    caches = await indicator.get_cache()
    assert len(caches) == 10
    for cache, day in zip(caches, chain(range(10, 16), range(18, 22))):
        assert cache.value.get("day") == day


@pytest.mark.anyio
async def test_incremental_get_continuous_cache_for_time_span(db_session):
    """Test getting continuous cache(s) for the incremental mixin."""

    class MyDailyIndicator(IncrementalCacheMixin, BaseIndicator):
        """Dummy indicator."""

        frame = "day"

        def get_lrs_query(
            self, since: datetime = None, until: datetime = None
        ) -> LRSQuery:
            return LRSQuery(query={"verb": "played", "since": since, "until": until})

        async def fetch_statements(self):
            pass

        async def compute(self, since: datetime = None, until: datetime = None):
            return {
                "day": since.day,
                "lrs_query": self.get_lrs_query(since=since, until=until).json(),
            }

        @staticmethod
        def merge(a: dict, b: dict):
            return (a, b)

    indicator = MyDailyIndicator(
        span_range=DatetimeRange(
            since=datetime(2023, 1, 1), until=datetime(2023, 1, 31)
        )
    )
    # Check that nothing already exists in the database
    caches = db_session.exec(
        select(CacheEntry).where(CacheEntry.key == indicator.cache_key)
    ).all()
    assert len(caches) == 0
    caches = await indicator.get_cache()
    assert len(caches) == 0

    # Create cache entries and check we can get them back
    for since, until in Arrow.span_range("day", Arrow(2023, 1, 10), Arrow(2023, 1, 15)):
        db_session.add(
            CacheEntry(
                key=indicator.cache_key,
                value={
                    "day": since.day,
                    "lrs_query": indicator.get_lrs_query(
                        since=since.datetime, until=until.datetime
                    ).json(),
                },
                since=since.datetime,
                until=until.datetime,
            )
        )
    db_session.commit()
    caches = await indicator._get_continuous_cache_for_time_span()
    assert len(caches) == 31
    assert len([c.value for c in caches if c.value is not None]) == 6


@pytest.mark.anyio
async def test_incremental_get_continuous_cache_for_time_span_with_week_frame(
    db_session,
):
    """Test getting continuous cache(s) for the incremental mixin with a week frame."""

    class MyWeeklyIndicator(IncrementalCacheMixin, BaseIndicator):
        """Dummy indicator."""

        frame = "week"

        def get_lrs_query(
            self, since: datetime = None, until: datetime = None
        ) -> LRSQuery:
            return LRSQuery(query={"verb": "played", "since": since, "until": until})

        async def fetch_statements(self):
            pass

        async def compute(self, since: datetime = None, until: datetime = None):
            return {
                "week": since.isocalendar()[1],
            }

        @staticmethod
        def merge(a: dict, b: dict):
            return (a, b)

    indicator = MyWeeklyIndicator(
        span_range=DatetimeRange(
            since=datetime(2023, 5, 12), until=datetime(2023, 7, 24)
        )
    )
    # Check that nothing already exists in the database
    caches = db_session.exec(
        select(CacheEntry).where(CacheEntry.key == indicator.cache_key)
    ).all()
    assert len(caches) == 0
    caches = await indicator.get_cache()
    assert len(caches) == 0

    # Create cache entries and check we can get them back
    for since, until in Arrow.span_range("week", Arrow(2023, 6, 1), Arrow(2023, 6, 30)):
        db_session.add(
            CacheEntry(
                key=indicator.cache_key,
                value={
                    "week": since.isocalendar()[1],
                },
                since=since.datetime,
                until=until.datetime,
            )
        )
    db_session.commit()
    caches = await indicator._get_continuous_cache_for_time_span()
    assert len(caches) == 12
    assert len([c.value for c in caches if c.value is not None]) == 5


@pytest.mark.anyio
async def test_incremental_merge():
    """Test merge method of the incremental mixin."""

    class MyDailyIndicator(IncrementalCacheMixin, BaseIndicator):
        """Dummy indicator."""

        frame = "day"

        def get_lrs_query(
            self, since: datetime = None, until: datetime = None
        ) -> LRSQuery:
            return LRSQuery(query={"verb": "played", "since": since, "until": until})

        async def fetch_statements(self):
            pass

        async def compute(self, since: datetime = None, until: datetime = None):
            return {
                "day": since.day,
                "lrs_query": self.get_lrs_query(since=since, until=until).json(),
            }

        @staticmethod
        def merge(a: tuple, b: tuple):
            return a + b

    assert MyDailyIndicator.merge((1, 2, 3), (4, 5, 6)) == (1, 2, 3, 4, 5, 6)


@pytest.mark.anyio
async def test_incremental_get_or_compute(db_session):
    """Test get or compute method of the incremental mixin."""

    class MyDailyIndicator(IncrementalCacheMixin, BaseIndicator):
        """Dummy indicator."""

        frame = "day"

        def get_lrs_query(
            self, since: datetime = None, until: datetime = None
        ) -> LRSQuery:
            return LRSQuery(query={"verb": "played", "since": since, "until": until})

        async def fetch_statements(self):
            pass

        async def compute(self, since: datetime = None, until: datetime = None):
            return {
                "day": since.day,
                "lrs_query": self.get_lrs_query(since=since, until=until).json(),
            }

        @staticmethod
        def merge(a: Union[dict, list], b: dict) -> list:
            if isinstance(a, dict):
                a = [a]
            return a + [b]

    indicator = MyDailyIndicator(
        span_range=DatetimeRange(
            since=datetime(2023, 1, 1), until=datetime(2023, 1, 31)
        )
    )
    # Check that nothing already exists in the database
    assert (
        len(
            db_session.exec(
                select(CacheEntry).where(CacheEntry.key == indicator.cache_key)
            ).all()
        )
        == 0
    )
    caches = db_session.exec(
        select(CacheEntry).where(CacheEntry.key == indicator.cache_key)
    ).all()
    assert len(caches) == 0
    caches = await indicator.get_cache()
    assert len(caches) == 0

    # Create cache entries and check we can get them back
    for since, until in chain(
        Arrow.span_range("day", Arrow(2023, 1, 10), Arrow(2023, 1, 15)),
        Arrow.span_range("day", Arrow(2023, 1, 18), Arrow(2023, 1, 21)),
    ):
        db_session.add(
            CacheEntry(
                key=indicator.cache_key,
                value={
                    "day": since.day,
                    "lrs_query": indicator.get_lrs_query(
                        since=since.datetime, until=until.datetime
                    ).json(),
                },
                since=since.datetime,
                until=until.datetime,
            )
        )
    db_session.commit()
    results = await indicator.get_or_compute()
    assert len(results) == 31
    assert [result.get("day") for result in results] == list(range(1, 32))
