"""Tests for video indicators."""
import json
import re
import urllib

import httpx
import pandas as pd
import pytest
from dateutil.tz import tzoffset
from pytest_httpx import HTTPXMock
from ralph.models.xapi.concepts.constants.video import RESULT_EXTENSION_TIME
from warren.backends import lrs_client
from warren.factories.base import BaseXapiStatementFactory
from warren.filters import DatetimeRange
from warren.models import DailyUniqueCount
from warren.xapi import StatementsTransformer
from warren_video.factories import VideoPlayedFactory
from warren_video.indicators import BaseDailyEvent, DailyEvent, DailyUniqueViews


def test_base_daily_event_subclass_verb_id():
    """Test '__init_subclass__' for the BaseDailyEvent class."""

    class MyIndicator(DailyEvent):
        verb_id = "test"

    # the __init_subclass__ is called when the class itself is constructed.
    # It should raise an error because the 'verb_id' class attribute is missing.
    with pytest.raises(TypeError) as exception:

        class MyIndicatorMissingAttribute(DailyEvent):
            wrong_attribute = "test"

    assert str(exception.value) == "Indicators must declare a 'verb_id' class attribute"


def test_base_daily_event_span_range_timezone():
    """Test 'to_span_range_timezone' for the BaseDailyEvent class."""
    # Create source statements
    raw_statements = [
        BaseXapiStatementFactory.build(
            mutations=[{"timestamp": "2023-01-01T00:10:00.000000+00:00"}]
        ).dict(),
        BaseXapiStatementFactory.build(
            mutations=[{"timestamp": "2023-01-03T00:10:00.000000+00:00"}]
        ).dict(),
    ]
    source_statements = StatementsTransformer.preprocess(raw_statements)

    class MyIndicator(BaseDailyEvent):
        def merge(self):
            pass

        def compute(self):
            pass

    # Create an indicator with a DateTimeRange in UTC
    indicator_utc = MyIndicator(
        span_range=DatetimeRange(since="2023-01-01", until="2023-01-03"),
        video_id="Test",
    )
    # Convert statements' timestamp
    statements = indicator_utc.to_span_range_timezone(source_statements)

    expected_statements = pd.to_datetime(
        pd.Series(
            [
                "2023-01-01T00:10:00+00:00",
                "2023-01-03T00:10:00+00:00",
            ],
            name="timestamp",
        )
    )

    # Statements' timestamp should be in UTC.
    assert statements["timestamp"].equals(expected_statements)

    # Create an indicator with a DateTimeRange in UTC+02:00
    indicator_with_timezone = MyIndicator(
        span_range=DatetimeRange(
            since="2023-01-01T00:00:00+02:00", until="2023-01-03T00:00:00+02:00"
        ),
        video_id="Test",
    )
    # Convert statements' timestamp
    statements = indicator_with_timezone.to_span_range_timezone(source_statements)

    # Statements' timestamp should be in UTC+02:00
    assert statements["timestamp"].equals(
        expected_statements.dt.tz_convert(tzoffset(None, 7200))
    )


def test_base_daily_event_add_date_column():
    """Test 'add_date_column' for the BaseDailyEvent class."""
    raw_statements = [
        BaseXapiStatementFactory.build(
            mutations=[{"timestamp": "2023-01-01T00:10:00.000000+00:00"}]
        ).dict(),
        BaseXapiStatementFactory.build(
            mutations=[{"timestamp": "2023-01-03T00:10:00.000000+00:00"}]
        ).dict(),
    ]
    source_statements = StatementsTransformer.preprocess(raw_statements)
    statements = BaseDailyEvent.extract_date_from_timestamp(source_statements)

    assert statements["date"].equals(
        pd.to_datetime(pd.Series(["2023-01-01", "2023-01-03"], name="date")).dt.date
    )
    assert "timestamp" not in statements.columns


@pytest.mark.anyio
async def test_daily_unique_views(httpx_mock: HTTPXMock, db_session):
    """Test the DailyUniqueViews indicator."""
    video_id = "uuid://ba4252ce-d042-43b0-92e8-f033f45612ee"

    local_template = VideoPlayedFactory.template
    local_template["object"]["id"] = video_id
    local_template["actor"] = {
        "mbox": "mailto:luke@sw.com",
        "objectType": "Agent",
        "name": "luke",
    }

    class LocalVideoPlayedFactory(VideoPlayedFactory):
        template: dict = local_template

    def lrs_response(request: httpx.Request):
        """Dynamic mock for the LRS response."""
        statements = []
        params = urllib.parse.parse_qs(request.url.query)
        if (
            params.get(b"since")[0] == b"2020-01-01T00:00:00+00:00"
            and params.get(b"until")[0] == b"2020-01-01T23:59:59.999999+00:00"
        ):
            statements = [
                json.loads(
                    LocalVideoPlayedFactory.build(
                        [
                            {
                                "result": {
                                    "extensions": {
                                        RESULT_EXTENSION_TIME: view_data["time"]
                                    }
                                }
                            },
                            {"timestamp": view_data["timestamp"]},
                        ]
                    ).json(),
                )
                for view_data in [
                    {"timestamp": "2020-01-01T00:00:00.000+00:00", "time": 17},
                    {"timestamp": "2020-01-01T00:00:30.000+00:00", "time": 23},
                ]
            ]
        elif (
            params.get(b"since")[0] == b"2020-01-02T00:00:00+00:00"
            and params.get(b"until")[0] == b"2020-01-02T23:59:59.999999+00:00"
        ):
            statements = [
                json.loads(
                    LocalVideoPlayedFactory.build(
                        [
                            {"result": {"extensions": {RESULT_EXTENSION_TIME: 300}}},
                            {"timestamp": "2020-01-02T00:00:00.000+00:00"},
                        ]
                    ).json(),
                )
            ]

        return httpx.Response(
            status_code=200,
            json={"statements": statements},
        )

    # Mock the LRS call so that it returns the fixture statements
    lrs_client.base_url = "http://fake-lrs.com"
    httpx_mock.add_callback(
        callback=lrs_response,
        url=re.compile(r"^http://fake-lrs\.com/xAPI/statements\?.*$"),
        method="GET",
    )

    span_range = DatetimeRange(since="2020-01-01", until="2020-01-03")
    indicator = DailyUniqueViews(video_id=video_id, span_range=span_range)
    daily_counts = await indicator.get_or_compute()

    # Generate an example statement to get default actor uid
    example_statements: pd.DataFrame = StatementsTransformer.preprocess(
        [json.loads(LocalVideoPlayedFactory.build().json())]
    )
    assert daily_counts.total == 1
    assert daily_counts.counts == [
        DailyUniqueCount(
            date="2020-01-01", count=1, users={example_statements["actor.uid"][0]}
        ),
        DailyUniqueCount(date="2020-01-02", count=0, users=set()),
        DailyUniqueCount(date="2020-01-03", count=0, users=set()),
    ]
