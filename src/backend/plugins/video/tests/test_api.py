"""Tests for the video API endpoints."""
import json
import re
from datetime import datetime

import pytest
from httpx import AsyncClient
from pytest_httpx import HTTPXMock
from ralph.models.xapi.concepts.constants.video import RESULT_EXTENSION_TIME
from ralph.models.xapi.concepts.verbs.video import PlayedVerb
from warren.backends import lrs_client
from warren.models import Response
from warren_video.factories import VideoPlayedFactory
from warren_video.models import VideoViews


@pytest.mark.anyio
@pytest.mark.parametrize(
    "video_id", ["foo", "foo/bar", "/foo/bar", "foo%2Fbar", "%2Ffoo%2Fbar"]
)
async def test_views_invalid_video_id(http_client: AsyncClient, video_id: str):
    """Test the video views endpoint with an invalid `video_id` path."""
    date_query_params = {
        "since": "2023-01-01",
        "until": "2023-01-31",
    }

    response = await http_client.get(
        f"/api/v1/video/{video_id}/views", params=date_query_params
    )

    assert response.status_code == 422
    assert "is not a valid 'IRI'." in response.json().get("detail")[0].get("msg")


@pytest.mark.anyio
async def test_views_valid_video_id_path_but_no_matching_video(
        http_client: AsyncClient, httpx_mock: HTTPXMock
):
    """Test the video views endpoint with a valid `video_id` but no results."""

    lrs_client.base_url = "http://fake-lrs.com"

    # Mock the call to the LRS so that it would return no statements (as it
    # would do with no matching video)
    httpx_mock.add_response(
        url=re.compile(r"^http://fake-lrs\.com/xAPI/statements\?.*$"),
        method="GET",
        json={"statements": []},
        status_code=200
    )

    response = await http_client.get(
        url="/api/v1/video/uuid://fake-uuid/views",
        params={
            "since": "2023-01-01",
            "until": "2023-01-01",
        },
    )

    assert response.status_code == 200
    assert VideoViews.parse_obj(response.json()) == VideoViews(
        total_views=0,
        views_count_by_date=[],
    )


@pytest.mark.anyio
async def test_views_backend_query(http_client: AsyncClient, httpx_mock: HTTPXMock):
    """Test the video views endpoint backend query results."""
    # Build 3 video statement fixtures
    view_1_date = "2020-01-01T00:00:00"
    view_1_time = datetime.fromisoformat(view_1_date).timestamp()
    view_2_date = "2020-01-01T00:00:30"
    view_2_time = datetime.fromisoformat(view_2_date).timestamp()
    view_3_date = "2020-01-02T00:00:00"
    view_3_time = datetime.fromisoformat(view_3_date).timestamp()
    video_uuid = "uuid://ba4252ce-d042-43b0-92e8-f033f45612ee"
    video_statements = [
        VideoPlayedFactory.build(
            [
                {"object": {"id": video_uuid, "objectType": "Activity"}},
                {"verb": {"id": PlayedVerb().id}},
                {"result": {"extensions": {RESULT_EXTENSION_TIME: video_time}}},
                {"timestamp": event_timestamp},
            ]
        )
        for video_time, event_timestamp in zip(
            [view_1_time, view_2_time, view_3_time],
            [view_1_date, view_2_date, view_3_date],
        )
    ]

    statements = [json.loads(statement.json()) for statement in video_statements]

    # Mock the LRS call so that it returns the fixture statements
    lrs_client.base_url = "http://fake-lrs.com"
    httpx_mock.add_response(
        url=re.compile(r"^http://fake-lrs\.com/xAPI/statements\?.*$"),
        method="GET",
        json={"statements": statements},
        status_code=200,
    )

    # Perform the call to warren backend. When fetching the LRS statements, it will
    # get the above mocked statements
    response = await http_client.get(
        url=f"/api/v1/video/{video_uuid}/views",
        params={
            "since": "2020-01-01",
            "until": "2020-01-03",
        },
    )

    assert response.status_code == 200

    video_views = (Response[VideoViews]).parse_obj(response.json()).content

    expected_video_views = {
        "total_views": 3,
        "views_count_by_date": [
            {"date": "2020-01-01", "count": 2},
            {"date": "2020-01-02", "count": 1},
        ],
    }

    assert video_views == expected_video_views
