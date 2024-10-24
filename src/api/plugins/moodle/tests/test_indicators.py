"""Tests for video indicators."""

import json
import re
import urllib
from unittest.mock import AsyncMock

import httpx
import pandas as pd
import pytest
from pytest_httpx import HTTPXMock
from warren.backends import lrs_client
from warren.filters import DatetimeRange
from warren.models import DailyCount, DailyUniqueCount
from warren.xapi import StatementsTransformer
from warren.xi.client import CRUDExperience
from warren.xi.enums import AggregationLevel
from warren.xi.exceptions import ExperienceIndexException
from warren.xi.factories import ExperienceFactory, RelationFactory
from warren.xi.models import ExperienceRead
from warren_moodle.factories import URLViewedFactory
from warren_moodle.indicators import CourseDailyMixin, DailyUniqueViews, DailyViews


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

        def get_activity_class(self):
            """Placeholder for get_activity_class."""
            pass

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

        def get_activity_class(self):
            """Placeholder for get_activity_class."""
            pass

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

        def get_activity_class(self):
            """Placeholder for get_activity_class."""
            pass

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
    monkeypatch,
):
    """Test fetch_activities raises an exception when content is not found for a
    source.
    """  # noqa: D205

    class TestCourseDailyMixin(CourseDailyMixin):
        """Test class inheriting from CourseDailyMixin for fetching activities."""

        def get_activity_class(self):
            """Placeholder for get_activity_class."""
            pass

        def get_views_indicator_class(self):
            """Placeholder for get_views_indicator_class."""
            pass

    course = ExperienceRead(
        **ExperienceFactory.build_dict(
            exclude=set(),
            id="ce0927fa-5f72-4623-9d29-37ef45c39609",
            aggregation_level=AggregationLevel.THREE,
            relations_target=[
                RelationFactory(**RelationFactory.build(id="123", source_id="222"))
            ],
        )
    )

    async def mock_get_course_content(object_id):
        """Mock function to simulate content not found for a specific source."""
        return None  # or raise an exception if you want to test for that

    # Simulate that the course is found, but the content is missing for "source1"
    xi_experience_get_mock = AsyncMock(side_effect=[course, mock_get_course_content])
    monkeypatch.setattr(CRUDExperience, "get", xi_experience_get_mock)

    mixin = TestCourseDailyMixin(
        course_id="course1", span_range="2024-01-01", modname="mod1"
    )

    with pytest.raises(
        ExperienceIndexException,
        match="Cannot find content with id source1 for course course1",
    ):
        await mixin.fetch_activities()
