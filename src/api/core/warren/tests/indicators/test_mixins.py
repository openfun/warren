"""Test indicators mixins."""

import hashlib
from datetime import datetime, timezone
from functools import cached_property
from itertools import chain
from typing import Union
from unittest.mock import AsyncMock

import pytest
from arrow import Arrow
from freezegun import freeze_time
from pydantic import BaseModel
from ralph.backends.lrs.base import LRSStatementsQuery
from sqlalchemy import func
from sqlalchemy.exc import MultipleResultsFound
from sqlmodel import select

from warren.filters import DatetimeRange
from warren.indicators.base import BaseIndicator
from warren.indicators.mixins import CacheMixin, IncrementalCacheMixin
from warren.indicators.models import CacheEntry


def test_cache_key_calculation():
    """Test the cache key calculation."""

    class MyIndicator(BaseIndicator, CacheMixin):
        """Dummy indicator."""

        def get_lrs_query(self) -> LRSStatementsQuery:
            return LRSStatementsQuery(verb="https://w3id.org/xapi/video/verbs/played")

        async def fetch_statements(self):
            pass

        async def compute(self):
            pass

    indicator = MyIndicator()
    lrs_query = '{"verb": "https://w3id.org/xapi/video/verbs/played"}'
    expected = f"myindicator-{hashlib.sha256(lrs_query.encode()).hexdigest()}"
    assert indicator.cache_key == expected


def test_cache_key_calculation_with_lrs_query_datetime_range():
    """Test the cache key calculation when the LRS query as date time range
    (since/until) parameters set.

    """  # noqa: D205

    class MyIndicator(BaseIndicator, CacheMixin):
        """Dummy indicator."""

        def get_lrs_query(self) -> LRSStatementsQuery:
            return LRSStatementsQuery(
                verb="https://w3id.org/xapi/video/verbs/played",
                since=datetime(2023, 1, 1),
                until=datetime(2023, 2, 1),
            )

        async def fetch_statements(self):
            pass

        async def compute(self):
            pass

    indicator = MyIndicator()
    # We exclude "since" and "until" parameters from the LRS query to calculate
    # the cache key
    lrs_query = '{"verb": "https://w3id.org/xapi/video/verbs/played"}'
    expected = f"myindicator-{hashlib.sha256(lrs_query.encode()).hexdigest()}"
    assert indicator.cache_key == expected


@pytest.mark.anyio
@freeze_time("2023-10-14")
async def test_save_with_single_cache_instance(db_session):
    """Test saving cached results to the database."""

    class MyIndicator(BaseIndicator, CacheMixin):
        """Dummy indicator."""

        def get_lrs_query(self) -> LRSStatementsQuery:
            return LRSStatementsQuery(verb="https://w3id.org/xapi/video/verbs/played")

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

    class MyIndicator(BaseIndicator, CacheMixin):
        """Dummy indicator."""

        def get_lrs_query(self) -> LRSStatementsQuery:
            return LRSStatementsQuery(verb="https://w3id.org/xapi/video/verbs/played")

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

    class MyIndicatorA(BaseIndicator, CacheMixin):
        """Dummy indicator."""

        def get_lrs_query(self) -> LRSStatementsQuery:
            return LRSStatementsQuery(verb="https://w3id.org/xapi/video/verbs/played")

        async def fetch_statements(self):
            pass

        async def compute(self):
            pass

    class MyIndicatorB(BaseIndicator, CacheMixin):
        """Dummy indicator."""

        def get_lrs_query(self) -> LRSStatementsQuery:
            return LRSStatementsQuery(verb="https://w3id.org/xapi/video/verbs/played")

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

    class MyIndicator(BaseIndicator, CacheMixin):
        """Dummy indicator."""

        def get_lrs_query(self) -> LRSStatementsQuery:
            return LRSStatementsQuery(verb="https://w3id.org/xapi/video/verbs/played")

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

    class MyIndicator(BaseIndicator, CacheMixin):
        """Dummy indicator."""

        def get_lrs_query(self) -> LRSStatementsQuery:
            return LRSStatementsQuery(verb="https://w3id.org/xapi/video/verbs/played")

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


def test_compute_annotation():
    """Test the _compute_annotation cached property."""

    class MyIndicator(BaseIndicator, CacheMixin):
        """Dummy indicator."""

        def get_lrs_query(self) -> LRSStatementsQuery:
            return None

        async def fetch_statements(self):
            pass

        async def compute(self):
            pass

    with pytest.raises(
        TypeError,
        match="compute method of an indicator should declare a return annotation",
    ):
        _ = MyIndicator()._compute_annotation

    class NewIndicator(MyIndicator):
        async def compute(self) -> list:
            pass

    assert NewIndicator()._compute_annotation == list


@pytest.mark.anyio
@pytest.mark.parametrize(
    "value",
    [
        '{"foo":"lol","bar":1}',
        {"foo": "lol", "bar": 1},
    ],
)
async def test_to_pydantic(value):
    """Test _to_pydantic method."""

    class MyType(BaseModel):
        foo: str
        bar: int

    class MyIndicator(BaseIndicator, CacheMixin):
        """Dummy indicator."""

        def get_lrs_query(self) -> LRSStatementsQuery:
            pass

        async def compute(self) -> MyType:
            pass

    indicator = MyIndicator()
    assert indicator._to_pydantic(indicator._compute_annotation, value) == MyType(
        foo="lol", bar=1
    )


@pytest.mark.anyio
@pytest.mark.parametrize(
    "value",
    [
        '{"foo":"lol","bar":1}',
        {"foo": "lol", "bar": 1},
    ],
)
async def test_raw_or_pydantic(value):
    """Test _raw_or_pydantic method."""

    class MyType(BaseModel):
        foo: str
        bar: int

    class MyIndicator(BaseIndicator, CacheMixin):
        """Dummy indicator."""

        def get_lrs_query(self) -> LRSStatementsQuery:
            pass

        async def compute(self) -> MyType:
            pass

    indicator = MyIndicator()
    assert indicator._raw_or_pydantic(value) == MyType(foo="lol", bar=1)

    class MyIndicator(BaseIndicator, CacheMixin):
        """Dummy indicator."""

        def get_lrs_query(self) -> LRSStatementsQuery:
            pass

        # For python >= 3.11, "Any" is recognized as a class:
        #
        # async def compute(self) -> Any:
        #
        # ... but not with prior versions, hence we fake return annotation with
        # anything that is not a Pydantic model so that we don't try to cast
        # computed result:
        async def compute(self) -> str:
            pass

    indicator = MyIndicator()
    assert indicator._raw_or_pydantic(value) == value


@pytest.mark.anyio
async def test_get_or_compute(db_session, monkeypatch):
    """Test getting cached results from the database or compute them."""

    class MyIndicator(BaseIndicator, CacheMixin):
        """Dummy indicator."""

        def get_lrs_query(self) -> LRSStatementsQuery:
            return LRSStatementsQuery(verb="https://w3id.org/xapi/video/verbs/played")

        async def fetch_statements(self):
            pass

        async def compute(self) -> dict:
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

    class MyIndicator(BaseIndicator, CacheMixin):
        """Dummy mocked indicator."""

        def get_lrs_query(self) -> LRSStatementsQuery:
            return LRSStatementsQuery(verb="https://w3id.org/xapi/video/verbs/played")

        async def fetch_statements(self):
            pass

        @cached_property
        def _compute_annotation(self):
            return dict

        compute = AsyncMock(return_value={"foo": [4, 5, 6]})

    indicator = MyIndicator()

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

    class MyDailyIndicator(BaseIndicator, IncrementalCacheMixin):
        """Dummy indicator."""

        frame = "day"

        def get_lrs_query(
            self, since: datetime = None, until: datetime = None
        ) -> LRSStatementsQuery:
            return LRSStatementsQuery(
                verb="https://w3id.org/xapi/video/verbs/played",
                since=since,
                until=until,
            )

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
    caches = await indicator.get_caches()
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

    caches = await indicator.get_caches()
    assert len(caches) == 10
    for cache, day in zip(caches, chain(range(10, 16), range(18, 22))):
        assert cache.value.get("day") == day


@pytest.mark.anyio
async def test_incremental_get_cache_when_multiple_cache_exists(db_session):
    """Test getting cache(s) for the incremental mixin with existing cache."""

    class MyDailyIndicator(BaseIndicator, IncrementalCacheMixin):
        """Dummy indicator."""

        frame = "day"

        def get_lrs_query(
            self, since: datetime = None, until: datetime = None
        ) -> LRSStatementsQuery:
            return LRSStatementsQuery(
                verb="https://w3id.org/xapi/video/verbs/played",
                since=since,
                until=until,
            )

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
    db_session.add(
        CacheEntry(
            key="foo", value=[1], since=datetime(2023, 1, 5), until=datetime(2023, 1, 6)
        )
    )
    db_session.add(
        CacheEntry(
            key="bar", value=[2], since=datetime(2013, 1, 3), until=datetime(2023, 1, 4)
        )
    )
    db_session.commit()
    caches = await indicator.get_caches()
    assert len(caches) == 10
    for cache, day in zip(caches, chain(range(10, 16), range(18, 22))):
        assert cache.value.get("day") == day


@pytest.mark.anyio
async def test_incremental_get_cache_limits(db_session):
    """Test getting cache(s) for the incremental mixin when querying date span range."""

    class MyDailyIndicator(BaseIndicator, IncrementalCacheMixin):
        """Dummy indicator."""

        frame = "day"

        def get_lrs_query(
            self, since: datetime = None, until: datetime = None
        ) -> LRSStatementsQuery:
            return LRSStatementsQuery(
                verb="https://w3id.org/xapi/video/verbs/played",
                since=since,
                until=until,
            )

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

    # Create a cache entry and check we can get it back
    for since, until in Arrow.span_range("day", Arrow(2023, 1, 1), Arrow(2023, 1, 31)):
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
    caches = db_session.exec(
        select(CacheEntry).where(CacheEntry.key == indicator.cache_key)
    ).all()
    assert len(caches) == 31

    caches = await indicator.get_caches()
    assert len(caches) == 31
    for cache, day in zip(caches, range(1, 31)):
        assert cache.value.get("day") == day


@pytest.mark.anyio
async def test_incremental_get_continuous_cache_for_time_span(db_session):
    """Test getting continuous cache(s) for the incremental mixin."""

    class MyDailyIndicator(BaseIndicator, IncrementalCacheMixin):
        """Dummy indicator."""

        frame = "day"

        def get_lrs_query(
            self, since: datetime = None, until: datetime = None
        ) -> LRSStatementsQuery:
            return LRSStatementsQuery(
                verb="https://w3id.org/xapi/video/verbs/played",
                since=since,
                until=until,
            )

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
    caches = await indicator.get_caches()
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
    caches = await indicator._get_continuous_caches_for_time_span()
    assert len(caches) == 31
    assert len([c.value for c in caches if c.value is not None]) == 6


@pytest.mark.anyio
async def test_incremental_get_continuous_cache_for_time_span_with_week_frame(
    db_session,
):
    """Test getting continuous cache(s) for the incremental mixin with a week frame."""

    class MyWeeklyIndicator(BaseIndicator, IncrementalCacheMixin):
        """Dummy indicator."""

        frame = "week"

        def get_lrs_query(
            self, since: datetime = None, until: datetime = None
        ) -> LRSStatementsQuery:
            return LRSStatementsQuery(
                verb="https://w3id.org/xapi/video/verbs/played",
                since=since,
                until=until,
            )

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
    caches = await indicator.get_caches()
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
    caches = await indicator._get_continuous_caches_for_time_span()
    assert len(caches) == 12
    assert len([c.value for c in caches if c.value is not None]) == 5


@pytest.mark.anyio
async def test_incremental_merge():
    """Test merge method of the incremental mixin."""

    class MyDailyIndicator(BaseIndicator, IncrementalCacheMixin):
        """Dummy indicator."""

        frame = "day"

        def get_lrs_query(
            self, since: datetime = None, until: datetime = None
        ) -> LRSStatementsQuery:
            return LRSStatementsQuery(
                verb="https://w3id.org/xapi/video/verbs/played",
                since=since,
                until=until,
            )

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
async def test_incremental_compute_annotation():
    """Test _compute_annotation property of the incremental mixin."""

    class MyDailyIndicator(BaseIndicator, IncrementalCacheMixin):
        """Dummy indicator."""

        frame = "day"

        def get_lrs_query(self) -> LRSStatementsQuery:
            pass

        async def compute(self) -> dict:
            return {}

        @staticmethod
        def merge(a, b) -> list:
            return []

    indicator = MyDailyIndicator(
        span_range=DatetimeRange(
            since=datetime(2023, 1, 1), until=datetime(2023, 1, 31)
        )
    )

    assert indicator._compute_annotation == dict

    class MyType(BaseModel):
        foo: str
        bar: dict

    class MyDailyIndicator(BaseIndicator, IncrementalCacheMixin):
        """Dummy indicator."""

        frame = "day"

        def get_lrs_query(self) -> LRSStatementsQuery:
            pass

        async def compute(self) -> MyType:
            return {}

        @staticmethod
        def merge(a, b) -> list:
            return []

    indicator = MyDailyIndicator(
        span_range=DatetimeRange(
            since=datetime(2023, 1, 1), until=datetime(2023, 1, 31)
        )
    )
    assert indicator._compute_annotation == MyType


@pytest.mark.anyio
@pytest.mark.parametrize(
    "values",
    [
        ['{"foo":"lol","bar":1}', '{"foo":"spam","bar":2}'],
        [{"foo": "lol", "bar": 1}, {"foo": "spam", "bar": 2}],
        ['{"foo":"lol","bar":1}', {"foo": "spam", "bar": 2}],
    ],
)
async def test_incremental_to_pydantic(values):
    """Test _to_pydantic method of the incremental mixin."""

    class MyType(BaseModel):
        foo: str
        bar: int

    class MyDailyIndicator(BaseIndicator, IncrementalCacheMixin):
        """Dummy indicator."""

        frame = "day"

        def get_lrs_query(self) -> LRSStatementsQuery:
            pass

        async def compute(self) -> MyType:
            pass

        @staticmethod
        def merge(a, b) -> list:
            pass

    indicator = MyDailyIndicator(
        span_range=DatetimeRange(
            since=datetime(2023, 1, 1), until=datetime(2023, 1, 31)
        )
    )
    assert [
        indicator._to_pydantic(indicator._compute_annotation, value) for value in values
    ] == [
        MyType(foo="lol", bar=1),
        MyType(foo="spam", bar=2),
    ]


@pytest.mark.anyio
async def test_incremental_get_or_compute(db_session):
    """Test get or compute method of the incremental mixin."""

    class MyDailyIndicator(BaseIndicator, IncrementalCacheMixin):
        """Dummy indicator."""

        frame = "day"

        def get_lrs_query(self) -> LRSStatementsQuery:
            return LRSStatementsQuery(
                verb="https://w3id.org/xapi/video/verbs/played",
                since=self.since,
                until=self.until,
            )

        async def fetch_statements(self):
            pass

        async def compute(self) -> dict:
            return {
                "day": self.since.day,
                "lrs_query": self.get_lrs_query().json(),
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
    caches = db_session.exec(
        select(CacheEntry).where(CacheEntry.key == indicator.cache_key)
    ).all()
    assert len(caches) == 0
    caches = await indicator.get_caches()
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
                    "lrs_query": MyDailyIndicator(
                        span_range=DatetimeRange(
                            since=since.datetime, until=until.datetime
                        )
                    )
                    .get_lrs_query()
                    .json(),
                },
                since=since.datetime,
                until=until.datetime,
            )
        )
    db_session.commit()
    caches = db_session.exec(
        select(CacheEntry).where(CacheEntry.key == indicator.cache_key)
    ).all()
    assert len(caches) == 10

    results = await indicator.get_or_compute()

    # We expect 31 results...
    assert len(results) == 31
    assert [result.get("day") for result in results] == list(range(1, 32))

    # ... stored in the database
    caches = db_session.exec(
        select(CacheEntry).where(CacheEntry.key == indicator.cache_key)
    ).all()
    assert len(caches) == 31


@pytest.mark.anyio
async def test_incremental_get_or_compute_update(db_session):
    """Test incremental cache update."""
    delta = 1

    class MyDailyIndicator(BaseIndicator, IncrementalCacheMixin):
        """Dummy indicator."""

        frame = "day"

        def get_lrs_query(self) -> LRSStatementsQuery:
            return LRSStatementsQuery(
                verb="https://w3id.org/xapi/video/verbs/played",
                since=self.since,
                until=self.until,
            )

        async def fetch_statements(self):
            pass

        async def compute(self) -> dict:
            return {
                "day": self.since.day,
                "views": self.since.day + delta,
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
    caches = db_session.exec(
        select(CacheEntry).where(CacheEntry.key == indicator.cache_key)
    ).all()
    assert len(caches) == 0
    caches = await indicator.get_caches()
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
                    "views": since.day + 1,
                },
                since=since.datetime,
                until=until.datetime,
            )
        )
    db_session.commit()
    assert (
        db_session.query(func.count())
        .select_from(CacheEntry)
        .filter(CacheEntry.key == indicator.cache_key)
        .scalar()
    ) == 10

    results = await indicator.get_or_compute()
    assert len(results) == 31
    assert [result.get("day") for result in results] == list(range(1, 32))
    assert [result.get("views") for result in results] == list(range(2, 33))

    delta = 2
    results = await indicator.get_or_compute(update=True)
    assert len(results) == 31
    assert [result.get("day") for result in results] == list(range(1, 32))
    assert [result.get("views") for result in results] == list(range(3, 34))

    cached = db_session.exec(
        select(CacheEntry)
        .where(CacheEntry.key == indicator.cache_key)
        .order_by(CacheEntry.since)
    ).all()
    assert len(cached) == 31
    assert cached[0].value == {"day": 1, "views": 3}


@pytest.mark.anyio
async def test_incremental_get_or_compute_update_and_create(db_session):
    """Test incremental cache update and creation at once.

    In this case we update existing entries and save new ones instead of
    updating all entries (see test_incremental_get_or_compute_update test).
    """
    delta = 2

    class MyDailyIndicator(BaseIndicator, IncrementalCacheMixin):
        """Dummy indicator."""

        frame = "day"

        def get_lrs_query(self) -> LRSStatementsQuery:
            return LRSStatementsQuery(
                verb="https://w3id.org/xapi/video/verbs/played",
                since=self.since,
                until=self.until,
            )

        async def fetch_statements(self):
            pass

        async def compute(self) -> dict:
            return {
                "day": self.since.day,
                "views": self.since.day + delta,
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
    caches = await indicator.get_caches()
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
                    "views": since.day + 1,
                },
                since=since.datetime,
                until=until.datetime,
            )
        )
    db_session.commit()
    results = await indicator.get_or_compute(update=True)
    assert len(results) == 31
    assert [result.get("day") for result in results] == list(range(1, 32))
    assert [result.get("views") for result in results] == list(range(3, 34))
