"""Tests for video indicators."""

import json
import re
import urllib
import urllib.parse
from datetime import date
from unittest.mock import AsyncMock

import httpx
import pandas as pd
import pytest
from pytest_httpx import HTTPXMock
from sqlmodel import Session
from warren.backends import lrs_client
from warren.filters import DatetimeRange
from warren.models import DailyCount, DailyCounts, DailyUniqueCount, DailyUniqueCounts
from warren.xapi import StatementsTransformer
from warren.xi.client import CRUDExperience
from warren.xi.enums import AggregationLevel
from warren.xi.exceptions import ExperienceIndexException
from warren.xi.factories import ExperienceFactory, RelationFactory
from warren.xi.models import ExperienceRead
from warren_moodle.factories import URLViewedFactory
from warren_moodle.indicators import (
    ActivityViewsCount,
    CourseDailyMixin,
    CourseDailyUniqueViews,
    CourseDailyViews,
    DailyUniqueViews,
    DailyViews,
)


@pytest.mark.anyio
async def test_daily_views(httpx_mock: HTTPXMock, db_session):
    """Test the DailyViews indicator to verify the total views and counts per day."""
    object_id = "uuid://ba4252ce-d042-43b0-92e8-f033f45612ee"

    local_template = URLViewedFactory.template
    local_template["object"]["id"] = object_id
    local_template["actor"] = {
        "mbox": "mailto:luke@sw.com",
        "objectType": "Agent",
        "name": "luke",
    }

    class LocalURLViewedFactory(URLViewedFactory):
        """Custom URLViewedFactory with a modified template for testing."""

        template: dict = local_template

    def lrs_response(request: httpx.Request):
        """Dynamic mock for the LRS response based on the request parameters."""
        statements = []
        params = urllib.parse.parse_qs(request.url.query)
        if (
            params.get(b"since")[0] == b"2020-01-01T00:00:00+00:00"
            and params.get(b"until")[0] == b"2020-01-01T23:59:59.999999+00:00"
        ):
            statements = [
                json.loads(
                    LocalURLViewedFactory.build(
                        [
                            {"timestamp": view_data["timestamp"]},
                        ]
                    ).json(),
                )
                for view_data in [
                    {"timestamp": "2020-01-01T00:00:00.000+00:00"},
                    {"timestamp": "2020-01-01T00:00:30.000+00:00"},
                ]
            ]
        elif (
            params.get(b"since")[0] == b"2020-01-02T00:00:00+00:00"
            and params.get(b"until")[0] == b"2020-01-02T23:59:59.999999+00:00"
        ):
            statements = [
                json.loads(
                    LocalURLViewedFactory.build(
                        [
                            {"timestamp": "2020-01-02T00:00:00.000+00:00"},
                        ]
                    ).json(),
                )
            ]

        return httpx.Response(
            status_code=200,
            json={"statements": statements},
        )

    lrs_client.base_url = "http://fake-lrs.com"
    lrs_client.settings.BASE_URL = "http://fake-lrs.com"
    httpx_mock.add_callback(
        callback=lrs_response,
        url=re.compile(r"^http://fake-lrs\.com/xAPI/statements\?.*$"),
        method="GET",
    )

    span_range = DatetimeRange(since="2020-01-01", until="2020-01-03")
    indicator = DailyViews(object_id=object_id, span_range=span_range)
    daily_counts = await indicator.get_or_compute()

    assert daily_counts.total == 3
    assert daily_counts.counts == [
        DailyCount(date="2020-01-01", count=2),
        DailyCount(date="2020-01-02", count=1),
        DailyCount(date="2020-01-03", count=0),
    ]


@pytest.mark.anyio
async def test_daily_unique_views(httpx_mock: HTTPXMock, db_session):
    """Test the DailyUniqueViews indicator to verify unique views per day."""
    object_id = "uuid://ba4252ce-d042-43b0-92e8-f033f45612ee"

    local_template = URLViewedFactory.template
    local_template["object"]["id"] = object_id
    local_template["actor"] = {
        "mbox": "mailto:luke@sw.com",
        "objectType": "Agent",
        "name": "luke",
    }

    class LocalURLViewedFactory(URLViewedFactory):
        """Custom URLViewedFactory with a modified template for testing unique views."""

        template: dict = local_template

    def lrs_response(request: httpx.Request):
        """Dynamic mock for the LRS response based on the request parameters."""
        statements = []
        params = urllib.parse.parse_qs(request.url.query)
        if (
            params.get(b"since")[0] == b"2020-01-01T00:00:00+00:00"
            and params.get(b"until")[0] == b"2020-01-01T23:59:59.999999+00:00"
        ):
            statements = [
                json.loads(
                    LocalURLViewedFactory.build(
                        [
                            {"timestamp": view_data["timestamp"]},
                        ]
                    ).json(),
                )
                for view_data in [
                    {"timestamp": "2020-01-01T00:00:00.000+00:00"},
                    {"timestamp": "2020-01-01T00:00:30.000+00:00"},
                ]
            ]
        elif (
            params.get(b"since")[0] == b"2020-01-02T00:00:00+00:00"
            and params.get(b"until")[0] == b"2020-01-02T23:59:59.999999+00:00"
        ):
            statements = [
                json.loads(
                    LocalURLViewedFactory.build(
                        [
                            {"timestamp": "2020-01-02T00:00:00.000+00:00"},
                        ]
                    ).json(),
                )
            ]

        return httpx.Response(
            status_code=200,
            json={"statements": statements},
        )

    lrs_client.base_url = "http://fake-lrs.com"
    lrs_client.settings.BASE_URL = "http://fake-lrs.com"
    httpx_mock.add_callback(
        callback=lrs_response,
        url=re.compile(r"^http://fake-lrs\.com/xAPI/statements\?.*$"),
        method="GET",
    )

    span_range = DatetimeRange(since="2020-01-01", until="2020-01-03")
    indicator = DailyUniqueViews(object_id=object_id, span_range=span_range)
    daily_counts = await indicator.get_or_compute()

    # Generate an example statement to get default actor uid
    example_statements: pd.DataFrame = StatementsTransformer.preprocess(
        [json.loads(LocalURLViewedFactory.build().json())]
    )
    assert daily_counts.total == 1
    assert daily_counts.counts == [
        DailyUniqueCount(
            date="2020-01-01", count=1, users={example_statements["actor.uid"][0]}
        ),
        DailyUniqueCount(date="2020-01-02", count=0, users=set()),
        DailyUniqueCount(date="2020-01-03", count=0, users=set()),
    ]


def test_course_daily_mixin_initialization():
    """Test initialization of CourseDailyMixin with course_id, span_range, and
    modname.
    """  # noqa: D205

    class TestCourseDailyMixin(CourseDailyMixin):
        """Test class inheriting from CourseDailyMixin for testing initialization."""

        def get_views_indicator_class(self):
            """Placeholder for get_views_indicator_class."""
            pass

    mixin = TestCourseDailyMixin(
        course_id="course1", span_range="2024-01-01", modname="mod1"
    )
    assert mixin.course_id == "course1"
    assert mixin.span_range == "2024-01-01"
    assert mixin.modname == "mod1"


@pytest.mark.anyio
async def test_course_daily_mixin_fetch_activities_from_unknown_course(monkeypatch):
    """Test fetch_activities raises an exception for an unknown course."""

    class TestCourseDailyMixin(CourseDailyMixin):
        """Test class inheriting from CourseDailyMixin for fetching activities."""

        def get_views_indicator_class(self):
            """Placeholder for get_views_indicator_class."""
            pass

    async def mock_get(object_id):
        return None

    monkeypatch.setattr(CRUDExperience, "get", AsyncMock(side_effect=mock_get))

    mixin = TestCourseDailyMixin(
        course_id="course1", span_range="2024-01-01", modname="mod1"
    )

    with pytest.raises(
        ExperienceIndexException,
        match="Unknown course course1. It should be indexed first!",
    ):
        await mixin.fetch_activities()


@pytest.mark.anyio
async def test_course_daily_mixin_fetch_activities_with_no_indexed_course_content(
    monkeypatch,
):
    """Test fetch_activities raises an exception when no content is indexed for
    the course.
    """  # noqa: D205

    class TestCourseDailyMixin(CourseDailyMixin):
        """Test class inheriting from CourseDailyMixin for fetching activities."""

        def get_views_indicator_class(self):
            """Placeholder for get_views_indicator_class."""
            pass

    course = ExperienceRead(
        **ExperienceFactory.build_dict(
            exclude=set(),
            id="ce0927fa-5f72-4623-9d29-37ef45c39609",
            aggregation_level=AggregationLevel.THREE,
            relations_target=[],
        )
    )
    xi_experience_get_mock = AsyncMock(return_value=course)
    monkeypatch.setattr(CRUDExperience, "get", xi_experience_get_mock)

    mixin = TestCourseDailyMixin(
        course_id="course1", span_range="2024-01-01", modname="mod1"
    )

    with pytest.raises(
        ExperienceIndexException, match="No content indexed for course course1"
    ):
        await mixin.fetch_activities()


@pytest.mark.anyio
async def test_course_daily_mixin_fetch_activities_course_content_not_found(
    db_session: Session,
    monkeypatch,
):
    """Test fetch_activities raises an exception when content is not found for a
    source.
    """  # noqa: D205
    RelationFactory.__session__ = db_session

    class TestCourseDailyMixin(CourseDailyMixin):
        """Test class inheriting from CourseDailyMixin for fetching activities."""

        def get_views_indicator_class(self):
            """Placeholder for get_views_indicator_class."""
            pass

    course = ExperienceRead(
        **ExperienceFactory.build_dict(
            exclude=set(),
            id="ce0927fa-5f72-4623-9d29-37ef45c39609",
            aggregation_level=AggregationLevel.THREE,
        )
    )
    relation = RelationFactory.build()
    course.relations_target = [relation]

    # Simulate that the course is found, but the content is missing for "source1"
    xi_experience_get_mock = AsyncMock(side_effect=[course, None])
    monkeypatch.setattr(CRUDExperience, "get", xi_experience_get_mock)

    mixin = TestCourseDailyMixin(
        course_id="course1", span_range="2024-01-01", modname="mod1"
    )

    with pytest.raises(
        ExperienceIndexException,
        match="Failed to find content for relation for course course1",
    ):
        await mixin.fetch_activities()


@pytest.mark.anyio
async def test_course_daily_mixin_fetch_activities_with_no_modname(
    db_session: Session,
    monkeypatch,
):
    """Test fetch_activities raises an exception when content is not found for a
    source.
    """  # noqa: D205
    RelationFactory.__session__ = db_session

    class TestCourseDailyMixin(CourseDailyMixin):
        """Test class inheriting from CourseDailyMixin for fetching activities."""

        def get_views_indicator_class(self):
            """Placeholder for get_views_indicator_class."""
            pass

    course = ExperienceRead(
        **ExperienceFactory.build_dict(
            exclude=set(),
            id="ce0927fa-5f72-4623-9d29-37ef45c39609",
            aggregation_level=AggregationLevel.THREE,
        )
    )
    course.relations_target = [RelationFactory.build() for _ in range(3)]

    contents = [
        ExperienceRead(
            **ExperienceFactory.build_dict(
                exclude=set(),
                id="ce0927fa-5f72-4623-9d29-37ef45c39609",
                aggregation_level=AggregationLevel.TWO,
                technical_datatypes=["mod_forum"],
            )
        )
        for _ in range(3)
    ]

    # Simulate that the course is found, but the content is missing for "source1"
    xi_experience_get_mock = AsyncMock(side_effect=[course] + contents)
    monkeypatch.setattr(CRUDExperience, "get", xi_experience_get_mock)

    indicator = TestCourseDailyMixin(course_id="course1", span_range="2024-01-01")

    activities = await indicator.fetch_activities()

    assert activities == contents


@pytest.mark.anyio
async def test_course_daily_mixin_fetch_activities_with_modname(
    db_session: Session,
    monkeypatch,
):
    """Test fetch_activities raises an exception when content is not found for a
    source.
    """  # noqa: D205
    RelationFactory.__session__ = db_session

    class TestCourseDailyMixin(CourseDailyMixin):
        """Test class inheriting from CourseDailyMixin for fetching activities."""

        def get_views_indicator_class(self):
            """Placeholder for get_views_indicator_class."""
            pass

    course = ExperienceRead(
        **ExperienceFactory.build_dict(
            exclude=set(),
            id="ce0927fa-5f72-4623-9d29-37ef45c39609",
            aggregation_level=AggregationLevel.THREE,
        )
    )
    course.relations_target = [RelationFactory.build() for _ in range(3)]

    contents = [
        ExperienceRead(
            **ExperienceFactory.build_dict(
                exclude=set(),
                id=relation.source_id,
                aggregation_level=AggregationLevel.TWO,
                technical_datatypes=["mod_url"],
                relations_source=[relation],
            )
        )
        for relation in course.relations_target[:2]
    ]
    contents.append(
        ExperienceRead(
            **ExperienceFactory.build_dict(
                exclude=set(),
                id=course.relations_target[2].source_id,
                aggregation_level=AggregationLevel.TWO,
                technical_datatypes=["mod_glossary"],
                relations_source=[course.relations_target[2]],
            )
        )
    )

    # Simulate that the course is found, but the content is missing for "source1"
    xi_experience_get_mock = AsyncMock(side_effect=[course] + contents)
    monkeypatch.setattr(CRUDExperience, "get", xi_experience_get_mock)

    indicator = TestCourseDailyMixin(
        course_id="course1", span_range="2024-01-01", modname="mod_glossary"
    )

    activities = await indicator.fetch_activities()

    glossary_contents = [
        content
        for content in contents
        if content.technical_datatypes[0] == "mod_glossary"
    ]

    assert activities == glossary_contents


@pytest.mark.anyio
async def test_course_daily_views_compute_with_no_modname(
    db_session: Session,
    httpx_mock: HTTPXMock,
    monkeypatch,
):
    """Test fetch_activities raises an exception when content is not found for a
    source.
    """  # noqa: D205
    RelationFactory.__session__ = db_session

    # Mock XI response
    course = ExperienceRead(
        **ExperienceFactory.build_dict(
            exclude=set(),
            id="ce0927fa-5f72-4623-9d29-37ef45c39609",
            aggregation_level=AggregationLevel.THREE,
        )
    )
    course.relations_target = [RelationFactory.build() for _ in range(3)]
    contents = [
        ExperienceRead(
            **ExperienceFactory.build_dict(
                exclude=set(),
                id=relation.source_id,
                aggregation_level=AggregationLevel.TWO,
                technical_datatypes=["mod_url"],
                relations_source=[relation],
            )
        )
        for relation in course.relations_target
    ]

    xi_experience_get_mock = AsyncMock(side_effect=[course] + contents)
    monkeypatch.setattr(CRUDExperience, "get", xi_experience_get_mock)

    # Mock LRS response
    content_iris = [content.iri for content in contents]

    def mock_lrs_response(request: httpx.Request):
        """Dynamic mock for the LRS response."""
        statements = []
        params = urllib.parse.parse_qs(request.url.query)
        activity_id = params.get(b"activity")[0]
        if (
            params.get(b"since")[0] == b"2020-01-01T00:00:00+00:00"
            and params.get(b"until")[0] == b"2020-01-01T23:59:59.999999+00:00"
        ):
            statements = [
                json.loads(
                    URLViewedFactory.build(
                        [
                            {"object": {"id": activity_id}},
                            {"timestamp": timestamp},
                        ]
                    ).json(),
                )
                for timestamp in [
                    "2020-01-01T00:00:00.000+00:00",
                    "2020-01-01T00:00:30.000+00:00",
                ]
            ]
        elif (
            params.get(b"since")[0] == b"2020-01-02T00:00:00+00:00"
            and params.get(b"until")[0] == b"2020-01-02T23:59:59.999999+00:00"
        ):
            statements = [
                json.loads(
                    URLViewedFactory.build(
                        [
                            {"object": {"id": activity_id}},
                            {"timestamp": "2020-01-02T00:00:00.000+00:00"},
                        ]
                    ).json(),
                )
            ]

        return httpx.Response(
            status_code=200,
            json={"statements": statements},
        )

    lrs_client.base_url = "http://fake-lrs.com"

    span_range = DatetimeRange(since="2020-01-01", until="2020-01-03")
    for iri in content_iris:
        activity_url = urllib.parse.quote(iri)
        httpx_mock.add_callback(
            callback=mock_lrs_response,
            url=re.compile(
                rf"^http://fake-lrs\.com/xAPI/statements\?.*activity={activity_url}.*$"
            ),
            method="GET",
        )

    indicator = CourseDailyViews(course_id="course1", span_range=span_range)
    views = await indicator.compute()

    assert len(views) == 3
    for daily_count, activity_id in zip(views, content_iris):
        assert daily_count == ActivityViewsCount(
            iri=activity_id,
            modname="mod_url",
            views=DailyCounts(
                total=3,
                counts=[
                    DailyCount(date=date(2020, 1, 1), count=2),
                    DailyCount(date=date(2020, 1, 2), count=1),
                    DailyCount(date=date(2020, 1, 3), count=0),
                ],
            ),
        )


@pytest.mark.anyio
async def test_course_daily_views_compute_with_modname(
    db_session: Session,
    httpx_mock: HTTPXMock,
    monkeypatch,
):
    """Test fetch_activities raises an exception when content is not found for a
    source.
    """  # noqa: D205
    RelationFactory.__session__ = db_session

    # Mock XI response
    course = ExperienceRead(
        **ExperienceFactory.build_dict(
            exclude=set(),
            id="ce0927fa-5f72-4623-9d29-37ef45c39609",
            aggregation_level=AggregationLevel.THREE,
        )
    )
    course.relations_target = [RelationFactory.build() for _ in range(3)]
    contents = [
        ExperienceRead(
            **ExperienceFactory.build_dict(
                exclude=set(),
                id=relation.source_id,
                aggregation_level=AggregationLevel.TWO,
                technical_datatypes=["mod_url"],
                relations_source=[relation],
            )
        )
        for relation in course.relations_target[:2]
    ]
    contents.append(
        ExperienceRead(
            **ExperienceFactory.build_dict(
                exclude=set(),
                id=course.relations_target[2].source_id,
                aggregation_level=AggregationLevel.TWO,
                technical_datatypes=["mod_book"],
                relations_source=[course.relations_target[2]],
            )
        )
    )

    xi_experience_get_mock = AsyncMock(side_effect=[course] + contents)
    monkeypatch.setattr(CRUDExperience, "get", xi_experience_get_mock)

    # Mock LRS response
    url_content_iris = [
        content.iri
        for content in contents
        if content.technical_datatypes == ["mod_url"]
    ]

    def mock_lrs_response(request: httpx.Request):
        """Dynamic mock for the LRS response."""
        statements = []
        params = urllib.parse.parse_qs(request.url.query)
        activity_id = params.get(b"activity")[0]
        if (
            params.get(b"since")[0] == b"2020-01-01T00:00:00+00:00"
            and params.get(b"until")[0] == b"2020-01-01T23:59:59.999999+00:00"
        ):
            statements = [
                json.loads(
                    URLViewedFactory.build(
                        [
                            {"object": {"id": activity_id}},
                            {"timestamp": timestamp},
                        ]
                    ).json(),
                )
                for timestamp in [
                    "2020-01-01T00:00:00.000+00:00",
                    "2020-01-01T00:00:30.000+00:00",
                ]
            ]
        elif (
            params.get(b"since")[0] == b"2020-01-02T00:00:00+00:00"
            and params.get(b"until")[0] == b"2020-01-02T23:59:59.999999+00:00"
        ):
            statements = [
                json.loads(
                    URLViewedFactory.build(
                        [
                            {"object": {"id": activity_id}},
                            {"timestamp": "2020-01-02T00:00:00.000+00:00"},
                        ]
                    ).json(),
                )
            ]

        return httpx.Response(
            status_code=200,
            json={"statements": statements},
        )

    lrs_client.base_url = "http://fake-lrs.com"

    span_range = DatetimeRange(since="2020-01-01", until="2020-01-03")
    for iri in url_content_iris:
        activity_url = urllib.parse.quote(iri)
        httpx_mock.add_callback(
            callback=mock_lrs_response,
            url=re.compile(
                rf"^http://fake-lrs\.com/xAPI/statements\?.*activity={activity_url}.*$"
            ),
            method="GET",
        )

    indicator = CourseDailyViews(
        course_id="course1", span_range=span_range, modname="mod_url"
    )
    views = await indicator.compute()

    assert len(views) == 2
    for daily_count, activity_id in zip(views, url_content_iris):
        assert daily_count == ActivityViewsCount(
            iri=activity_id,
            modname="mod_url",
            views=DailyCounts(
                total=3,
                counts=[
                    DailyCount(date=date(2020, 1, 1), count=2),
                    DailyCount(date=date(2020, 1, 2), count=1),
                    DailyCount(date=date(2020, 1, 3), count=0),
                ],
            ),
        )


@pytest.mark.anyio
async def test_course_daily_unique_views_compute_with_no_modname(
    db_session: Session,
    httpx_mock: HTTPXMock,
    monkeypatch,
):
    """Test fetch_activities raises an exception when content is not found for a
    source.
    """  # noqa: D205
    RelationFactory.__session__ = db_session

    local_template = URLViewedFactory.template
    local_template["actor"] = {
        "mbox": "mailto:luke@sw.com",
        "objectType": "Agent",
        "name": "luke",
    }

    class LocalURLViewedFactory(URLViewedFactory):
        template: dict = local_template

    # Mock XI response
    course = ExperienceRead(
        **ExperienceFactory.build_dict(
            exclude=set(),
            id="ce0927fa-5f72-4623-9d29-37ef45c39609",
            aggregation_level=AggregationLevel.THREE,
        )
    )
    course.relations_target = [RelationFactory.build() for _ in range(3)]
    contents = [
        ExperienceRead(
            **ExperienceFactory.build_dict(
                exclude=set(),
                id=relation.source_id,
                aggregation_level=AggregationLevel.TWO,
                technical_datatypes=["mod_url"],
                relations_source=[relation],
            )
        )
        for relation in course.relations_target
    ]

    xi_experience_get_mock = AsyncMock(side_effect=[course] + contents)
    monkeypatch.setattr(CRUDExperience, "get", xi_experience_get_mock)

    # Mock LRS response
    content_iris = [content.iri for content in contents]

    def mock_lrs_response(request: httpx.Request):
        """Dynamic mock for the LRS response."""
        statements = []
        params = urllib.parse.parse_qs(request.url.query)
        activity_id = params.get(b"activity")[0]
        if (
            params.get(b"since")[0] == b"2020-01-01T00:00:00+00:00"
            and params.get(b"until")[0] == b"2020-01-01T23:59:59.999999+00:00"
        ):
            statements = [
                json.loads(
                    LocalURLViewedFactory.build(
                        [
                            {"object": {"id": activity_id}},
                            {"timestamp": timestamp},
                        ]
                    ).json(),
                )
                for timestamp in [
                    "2020-01-01T00:00:00.000+00:00",
                    "2020-01-01T00:00:30.000+00:00",
                ]
            ]
        elif (
            params.get(b"since")[0] == b"2020-01-02T00:00:00+00:00"
            and params.get(b"until")[0] == b"2020-01-02T23:59:59.999999+00:00"
        ):
            statements = [
                json.loads(
                    LocalURLViewedFactory.build(
                        [
                            {"object": {"id": activity_id}},
                            {"timestamp": "2020-01-02T00:00:00.000+00:00"},
                        ]
                    ).json(),
                )
            ]

        return httpx.Response(
            status_code=200,
            json={"statements": statements},
        )

    lrs_client.base_url = "http://fake-lrs.com"

    span_range = DatetimeRange(since="2020-01-01", until="2020-01-03")
    for iri in content_iris:
        activity_url = urllib.parse.quote(iri)
        httpx_mock.add_callback(
            callback=mock_lrs_response,
            url=re.compile(
                rf"^http://fake-lrs\.com/xAPI/statements\?.*activity={activity_url}.*$"
            ),
            method="GET",
        )

    indicator = CourseDailyUniqueViews(course_id="course1", span_range=span_range)
    views = await indicator.compute()

    # Generate an example statement to get default actor uid
    example_statements: pd.DataFrame = StatementsTransformer.preprocess(
        [json.loads(LocalURLViewedFactory.build().json())]
    )
    assert len(views) == 3
    for daily_count, activity_id in zip(views, content_iris):
        assert daily_count == ActivityViewsCount(
            iri=activity_id,
            modname="mod_url",
            views=DailyUniqueCounts(
                total=1,
                counts=[
                    DailyUniqueCount(
                        date=date(2020, 1, 1),
                        count=1,
                        users={example_statements["actor.uid"][0]},
                    ),
                    DailyUniqueCount(
                        date=date(2020, 1, 2),
                        count=0,
                        users=set(),
                    ),
                    DailyUniqueCount(date=date(2020, 1, 3), count=0, users=set()),
                ],
            ),
        )


@pytest.mark.anyio
async def test_course_daily_unique_views_compute_with_modname(
    db_session: Session,
    httpx_mock: HTTPXMock,
    monkeypatch,
):
    """Test fetch_activities raises an exception when content is not found for a
    source.
    """  # noqa: D205
    RelationFactory.__session__ = db_session

    local_template = URLViewedFactory.template
    local_template["actor"] = {
        "mbox": "mailto:luke@sw.com",
        "objectType": "Agent",
        "name": "luke",
    }

    class LocalURLViewedFactory(URLViewedFactory):
        template: dict = local_template

    # Mock XI response
    course = ExperienceRead(
        **ExperienceFactory.build_dict(
            exclude=set(),
            id="ce0927fa-5f72-4623-9d29-37ef45c39609",
            aggregation_level=AggregationLevel.THREE,
        )
    )
    course.relations_target = [RelationFactory.build() for _ in range(3)]
    contents = [
        ExperienceRead(
            **ExperienceFactory.build_dict(
                exclude=set(),
                id=relation.source_id,
                aggregation_level=AggregationLevel.TWO,
                technical_datatypes=["mod_url"],
                relations_source=[relation],
            )
        )
        for relation in course.relations_target[:2]
    ]
    contents.append(
        ExperienceRead(
            **ExperienceFactory.build_dict(
                exclude=set(),
                id=course.relations_target[2].source_id,
                aggregation_level=AggregationLevel.TWO,
                technical_datatypes=["mod_book"],
                relations_source=[course.relations_target[2]],
            )
        )
    )

    xi_experience_get_mock = AsyncMock(side_effect=[course] + contents)
    monkeypatch.setattr(CRUDExperience, "get", xi_experience_get_mock)
    # Mock LRS response
    url_content_iris = [
        content.iri
        for content in contents
        if content.technical_datatypes == ["mod_url"]
    ]

    def mock_lrs_response(request: httpx.Request):
        """Dynamic mock for the LRS response."""
        statements = []
        params = urllib.parse.parse_qs(request.url.query)
        activity_id = params.get(b"activity")[0]
        if (
            params.get(b"since")[0] == b"2020-01-01T00:00:00+00:00"
            and params.get(b"until")[0] == b"2020-01-01T23:59:59.999999+00:00"
        ):
            statements = [
                json.loads(
                    LocalURLViewedFactory.build(
                        [
                            {"object": {"id": activity_id}},
                            {"timestamp": timestamp},
                        ]
                    ).json(),
                )
                for timestamp in [
                    "2020-01-01T00:00:00.000+00:00",
                    "2020-01-01T00:00:30.000+00:00",
                ]
            ]
        elif (
            params.get(b"since")[0] == b"2020-01-02T00:00:00+00:00"
            and params.get(b"until")[0] == b"2020-01-02T23:59:59.999999+00:00"
        ):
            statements = [
                json.loads(
                    LocalURLViewedFactory.build(
                        [
                            {"object": {"id": activity_id}},
                            {"timestamp": "2020-01-02T00:00:00.000+00:00"},
                        ]
                    ).json(),
                )
            ]

        return httpx.Response(
            status_code=200,
            json={"statements": statements},
        )

    lrs_client.base_url = "http://fake-lrs.com"

    span_range = DatetimeRange(since="2020-01-01", until="2020-01-03")
    for iri in url_content_iris:
        activity_url = urllib.parse.quote(iri)
        httpx_mock.add_callback(
            callback=mock_lrs_response,
            url=re.compile(
                rf"^http://fake-lrs\.com/xAPI/statements\?.*activity={activity_url}.*$"
            ),
            method="GET",
        )

    indicator = CourseDailyUniqueViews(
        course_id="course1", span_range=span_range, modname="mod_url"
    )
    views = await indicator.compute()

    # Generate an example statement to get default actor uid
    example_statements: pd.DataFrame = StatementsTransformer.preprocess(
        [json.loads(LocalURLViewedFactory.build().json())]
    )
    assert len(views) == 2
    for daily_count, activity_id in zip(views, url_content_iris):
        assert daily_count == ActivityViewsCount(
            iri=activity_id,
            modname="mod_url",
            views=DailyUniqueCounts(
                total=1,
                counts=[
                    DailyUniqueCount(
                        date=date(2020, 1, 1),
                        count=1,
                        users={example_statements["actor.uid"][0]},
                    ),
                    DailyUniqueCount(
                        date=date(2020, 1, 2),
                        count=0,
                        users=set(),
                    ),
                    DailyUniqueCount(date=date(2020, 1, 3), count=0, users=set()),
                ],
            ),
        )
