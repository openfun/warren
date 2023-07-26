"""Tests for the video API endpoints."""
import json
import re

import pytest
from httpx import AsyncClient
from pytest_httpx import HTTPXMock
from ralph.models.xapi.concepts.constants.video import RESULT_EXTENSION_TIME
from ralph.models.xapi.concepts.verbs.tincan_vocabulary import DownloadedVerb
from ralph.models.xapi.concepts.verbs.video import PlayedVerb
from warren.backends import lrs_client
from warren.models import DailyCounts, Response
from warren_video.factories import VideoDownloadedFactory, VideoPlayedFactory


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

    # Mock the call to the LRS so that it would return no statements, as it
    # would do with no matching video
    httpx_mock.add_response(
        url=re.compile(r"^http://fake-lrs\.com/xAPI/statements\?.*$"),
        method="GET",
        json={"statements": []},
        status_code=200,
    )

    response = await http_client.get(
        url="/api/v1/video/uuid://fake-uuid/views",
        params={
            "since": "2023-01-01",
            "until": "2023-01-01",
        },
    )

    assert response.status_code == 200
    assert DailyCounts.parse_obj(response.json()) == DailyCounts(
        total_count=0,
        count_by_date=[],
    )


@pytest.mark.anyio
async def test_views_backend_query(http_client: AsyncClient, httpx_mock: HTTPXMock):
    """Test the video views endpoint backend query results."""
    # Define 3 video views fixtures
    video_id = "uuid://ba4252ce-d042-43b0-92e8-f033f45612ee"
    video_views_fixtures = [
        {"timestamp": "2020-01-01T00:00:00.000+00:00", "time": 100},
        {"timestamp": "2020-01-01T00:00:30.000+00:00", "time": 200},
        {"timestamp": "2020-01-02T00:00:00.000+00:00", "time": 300},
    ]

    # Build video statements from fixtures
    video_statements = [
        VideoPlayedFactory.build(
            [
                {"object": {"id": video_id, "objectType": "Activity"}},
                {"verb": {"id": PlayedVerb().id}},
                {"result": {"extensions": {RESULT_EXTENSION_TIME: view_data["time"]}}},
                {"timestamp": view_data["timestamp"]},
            ]
        )
        for view_data in video_views_fixtures
    ]

    # Convert each video statement to a JSON object
    video_statements_json = [
        json.loads(statement.json()) for statement in video_statements
    ]

    # Mock the LRS call so that it returns the fixture statements
    lrs_client.base_url = "http://fake-lrs.com"
    httpx_mock.add_response(
        url=re.compile(r"^http://fake-lrs\.com/xAPI/statements\?.*$"),
        method="GET",
        json={"statements": video_statements_json},
        status_code=200,
    )

    # Perform the call to warren backend. When fetching the LRS statements, it will
    # get the above mocked statements
    response = await http_client.get(
        url=f"/api/v1/video/{video_id}/views",
        params={
            "since": "2020-01-01",
            "until": "2020-01-03",
        },
    )

    assert response.status_code == 200

    # Parse the response to obtain video views count_by_date
    video_views = (Response[DailyCounts]).parse_obj(response.json()).content

    # Counting all views is expected
    expected_video_views = {
        "total_count": 3,
        "count_by_date": [
            {"date": "2020-01-01", "count": 2},
            {"date": "2020-01-02", "count": 1},
        ],
    }

    assert video_views == expected_video_views


@pytest.mark.anyio
async def test_unique_views_backend_query(
    http_client: AsyncClient, httpx_mock: HTTPXMock
):
    """Test the video views endpoint, with parameter unique=True."""
    # Define 3 video views fixtures
    video_id = "uuid://ba4252ce-d042-43b0-92e8-f033f45612ee"
    video_views_fixtures = [
        {"timestamp": "2020-01-01T00:00:00.000+00:00", "time": 100},
        {"timestamp": "2020-01-01T00:00:30.000+00:00", "time": 200},
        {"timestamp": "2020-01-02T00:00:00.000+00:00", "time": 300},
    ]

    # Build video statements from fixtures
    video_statements = [
        VideoPlayedFactory.build(
            [
                {
                    "actor": {
                        "objectType": "Agent",
                        "account": {"name": "John", "homePage": "http://fun-mooc.fr"},
                    }
                },
                {"object": {"id": video_id, "objectType": "Activity"}},
                {"verb": {"id": PlayedVerb().id}},
                {"result": {"extensions": {RESULT_EXTENSION_TIME: view_data["time"]}}},
                {"timestamp": view_data["timestamp"]},
            ]
        )
        for view_data in video_views_fixtures
    ]

    # Convert each video statement to a JSON object
    video_statements_json = [
        json.loads(statement.json()) for statement in video_statements
    ]

    # Mock the LRS call so that it returns the fixture statements
    lrs_client.base_url = "http://fake-lrs.com"
    httpx_mock.add_response(
        url=re.compile(r"^http://fake-lrs\.com/xAPI/statements\?.*$"),
        method="GET",
        json={"statements": video_statements_json},
        status_code=200,
    )

    # Perform the call to warren backend. When fetching the LRS statements, it will
    # get the above mocked statements
    response = await http_client.get(
        url=f"/api/v1/video/{video_id}/views?unique=true",
        params={
            "since": "2020-01-01",
            "until": "2020-01-03",
        },
    )

    assert response.status_code == 200

    # Parse the response to obtain video views count_by_date
    video_views = (Response[DailyCounts]).parse_obj(response.json()).content

    # Counting only the first view is expected
    expected_video_views = {
        "total_count": 1,
        "count_by_date": [
            {"date": "2020-01-01", "count": 1},
        ],
    }

    assert video_views == expected_video_views


@pytest.mark.anyio
@pytest.mark.parametrize(
    "video_id", ["foo", "foo/bar", "/foo/bar", "foo%2Fbar", "%2Ffoo%2Fbar"]
)
async def test_downloads_invalid_video_id(http_client: AsyncClient, video_id: str):
    """Test the video downloads endpoint with an invalid `video_id` path."""
    date_query_params = {
        "since": "2023-01-01",
        "until": "2023-01-31",
    }

    response = await http_client.get(
        f"/api/v1/video/{video_id}/downloads", params=date_query_params
    )

    assert response.status_code == 422
    assert "is not a valid 'IRI'." in response.json().get("detail")[0].get("msg")


@pytest.mark.anyio
async def test_downloads_valid_video_id_path_but_no_matching_video(
    http_client: AsyncClient, httpx_mock: HTTPXMock
):
    """Test the video downloads endpoint with a valid `video_id` but no results."""
    lrs_client.base_url = "http://fake-lrs.com"

    # Mock the call to the LRS so that it would return no statements, as it
    # would do with no matching video
    httpx_mock.add_response(
        url=re.compile(r"^http://fake-lrs\.com/xAPI/statements\?.*$"),
        method="GET",
        json={"statements": []},
        status_code=200,
    )

    response = await http_client.get(
        url="/api/v1/video/uuid://fake-uuid/downloads",
        params={
            "since": "2023-01-01",
            "until": "2023-01-01",
        },
    )

    assert response.status_code == 200
    assert DailyCounts.parse_obj(response.json()) == DailyCounts(
        total_count=0,
        count_by_date=[],
    )


@pytest.mark.anyio
async def test_downloads_backend_query(http_client: AsyncClient, httpx_mock: HTTPXMock):
    """Test the video downloads endpoint backend query results."""
    # Define 3 video downloads fixtures
    video_id = "uuid://ba4252ce-d042-43b0-92e8-f033f45612ee"
    video_download_timestamps = [
        "2020-01-01T00:00:00.000+00:00",
        "2020-01-01T00:00:30.000+00:00",
        "2020-01-02T00:00:00.000+00:00",
    ]

    # Build video statements from fixtures
    video_statements = [
        VideoDownloadedFactory.build(
            [
                {"object": {"id": video_id, "objectType": "Activity"}},
                {"verb": {"id": DownloadedVerb().id}},
                {"timestamp": download_timestamp},
            ]
        )
        for download_timestamp in video_download_timestamps
    ]

    # Convert each video statement to a JSON object
    video_statements_json = [
        json.loads(statement.json()) for statement in video_statements
    ]

    # Mock the LRS call so that it returns the fixture statements
    lrs_client.base_url = "http://fake-lrs.com"
    httpx_mock.add_response(
        url=re.compile(r"^http://fake-lrs\.com/xAPI/statements\?.*$"),
        method="GET",
        json={"statements": video_statements_json},
        status_code=200,
    )

    # Perform the call to warren backend. When fetching the LRS statements, it will
    # get the above mocked statements
    response = await http_client.get(
        url=f"/api/v1/video/{video_id}/downloads",
        params={
            "since": "2020-01-01",
            "until": "2020-01-03",
        },
    )

    assert response.status_code == 200

    # Parse the response to obtain video downloads count_by_date
    video_downloads = (Response[DailyCounts]).parse_obj(response.json()).content

    # Counting all downloads is expected
    expected_video_downloads = {
        "total_count": 3,
        "count_by_date": [
            {"date": "2020-01-01", "count": 2},
            {"date": "2020-01-02", "count": 1},
        ],
    }

    assert video_downloads == expected_video_downloads


@pytest.mark.anyio
async def test_unique_downloads_backend_query(
    http_client: AsyncClient, httpx_mock: HTTPXMock
):
    """Test the video downloads endpoint, with parameter unique=True."""
    # Define 3 video views fixtures
    video_id = "uuid://ba4252ce-d042-43b0-92e8-f033f45612ee"
    video_download_timestamps = [
        "2020-01-01T00:00:00.000+00:00",
        "2020-01-01T00:00:30.000+00:00",
        "2020-01-02T00:00:00.000+00:00",
    ]

    # Build video statements from fixtures
    video_statements = [
        VideoDownloadedFactory.build(
            [
                {
                    "actor": {
                        "objectType": "Agent",
                        "account": {"name": "John", "homePage": "http://fun-mooc.fr"},
                    }
                },
                {"object": {"id": video_id, "objectType": "Activity"}},
                {"verb": {"id": DownloadedVerb().id}},
                {"timestamp": download_timestamp},
            ]
        )
        for download_timestamp in video_download_timestamps
    ]

    # Convert each video statement to a JSON object
    video_statements_json = [
        json.loads(statement.json()) for statement in video_statements
    ]

    # Mock the LRS call so that it returns the fixture statements
    lrs_client.base_url = "http://fake-lrs.com"
    httpx_mock.add_response(
        url=re.compile(r"^http://fake-lrs\.com/xAPI/statements\?.*$"),
        method="GET",
        json={"statements": video_statements_json},
        status_code=200,
    )

    # Perform the call to warren backend. When fetching the LRS statements, it will
    # get the above mocked statements
    response = await http_client.get(
        url=f"/api/v1/video/{video_id}/downloads?unique=true",
        params={
            "since": "2020-01-01",
            "until": "2020-01-03",
        },
    )

    assert response.status_code == 200

    # Parse the response to obtain video downloads count_by_date
    video_downloads = (Response[DailyCounts]).parse_obj(response.json()).content

    # Counting only the first download is expected
    expected_video_downloads = {
        "total_count": 1,
        "count_by_date": [
            {"date": "2020-01-01", "count": 1},
        ],
    }

    assert video_downloads == expected_video_downloads
