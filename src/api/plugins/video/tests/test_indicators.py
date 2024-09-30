"""Tests for video indicators."""

import json
import re
import urllib

import httpx
import pandas as pd
import pytest
from pytest_httpx import HTTPXMock
from ralph.models.xapi.concepts.constants.video import RESULT_EXTENSION_TIME
from warren.backends import lrs_client
from warren.filters import DatetimeRange
from warren.models import DailyUniqueCount
from warren.xapi import StatementsTransformer
from warren_video.factories import VideoPlayedFactory
from warren_video.indicators import DailyUniqueViews


@pytest.mark.anyio
async def test_daily_unique_views(httpx_mock: HTTPXMock, db_session):
    """Test the DailyUniqueViews indicator."""
    object_id = "uuid://ba4252ce-d042-43b0-92e8-f033f45612ee"

    local_template = VideoPlayedFactory.template
    local_template["object"]["id"] = object_id
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
