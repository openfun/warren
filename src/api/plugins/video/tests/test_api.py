"""Tests for the video API endpoints."""
import json
import re
import urllib

import httpx
import pytest
from pytest_httpx import HTTPXMock
from ralph.models.xapi.concepts.constants.video import RESULT_EXTENSION_TIME
from warren.backends import lrs_client
from warren_video.factories import LMSDownloadedVideoFactory, VideoPlayedFactory


@pytest.mark.anyio
@pytest.mark.parametrize(
    "video_id", ["foo", "foo/bar", "/foo/bar", "foo%2Fbar", "%2Ffoo%2Fbar"]
)
async def test_views_invalid_video_id(
    http_client: httpx.AsyncClient, auth_headers: dict, video_id: str
):
    """Test the video views endpoint with an invalid `video_id` path."""
    date_query_params = {
        "since": "2023-01-01",
        "until": "2023-01-31",
    }

    response = await http_client.get(
        f"/api/v1/video/{video_id}/views",
        params=date_query_params,
        headers=auth_headers,
    )

    assert response.status_code == 422
    assert "is not a valid 'IRI'." in response.json().get("detail")[0].get("msg")


@pytest.mark.anyio
async def test_views_valid_video_id_path_but_no_matching_video(
    http_client: httpx.AsyncClient,
    httpx_mock: HTTPXMock,
    auth_headers: dict,
    db_session,
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
        headers=auth_headers,
    )

    assert response.status_code == 200

    # Counting all views is expected
    expected_video_views = {
        "total": 0,
        "counts": [
            {"date": "2023-01-01", "count": 0},
        ],
    }

    assert response.json() == expected_video_views


@pytest.mark.anyio
async def test_views_invalid_auth_headers(http_client: httpx.AsyncClient):
    """Test the video views endpoint with an invalid `auth_headers`."""
    response = await http_client.get(
        url="/api/v1/video/uuid://fake-uuid/views",
        params={
            "since": "2023-01-01",
            "until": "2023-01-01",
        },
        headers={"Authorization": "Bearer Wrong_Token"},
    )

    assert response.status_code == 401
    assert response.json().get("detail") == "Could not validate credentials"


@pytest.mark.anyio
async def test_views_missing_auth_headers(http_client: httpx.AsyncClient):
    """Test the video views endpoint with missing `auth_headers`."""
    response = await http_client.get(
        url="/api/v1/video/uuid://fake-uuid/views",
        params={
            "since": "2023-01-01",
            "until": "2023-01-01",
        },
    )

    assert response.status_code == 401
    assert response.json().get("detail") == "Not authenticated"


@pytest.mark.anyio
async def test_views_backend_query(
    http_client: httpx.AsyncClient,
    httpx_mock: HTTPXMock,
    auth_headers: dict,
    db_session,
):
    """Test the video views endpoint backend query results."""
    # Define 3 video views fixtures
    video_id = "uuid://ba4252ce-d042-43b0-92e8-f033f45612ee"
    local_template = VideoPlayedFactory.template
    local_template["object"]["id"] = video_id

    class LocalVideoPlayedFactory(VideoPlayedFactory):
        template: dict = local_template

    def lrs_response(request: httpx.Request):
        """Dynamic mock for the LRS response."""
        statements = []
        params = urllib.parse.parse_qs(request.url.query)
        if (
            params.get(b"since")[0] == b"2020-01-01 00:00:00+05:00"
            and params.get(b"until")[0] == b"2020-01-01 23:59:59.999999+05:00"
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
                    {"timestamp": "2019-12-31 20:00:00.000+00:00", "time": 3},
                    {"timestamp": "2020-01-01 00:00:00.000+00:00", "time": 23},
                    {"timestamp": "2020-01-01 00:00:30.000+00:00", "time": 18},
                ]
            ]
        elif (
            params.get(b"since")[0] == b"2020-01-02 00:00:00+05:00"
            and params.get(b"until")[0] == b"2020-01-02 23:59:59.999999+05:00"
        ):
            statements = [
                json.loads(
                    LocalVideoPlayedFactory.build(
                        [
                            {"result": {"extensions": {RESULT_EXTENSION_TIME: 5}}},
                            {"timestamp": "2020-01-02 00:00:00.000+00:00"},
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

    # Perform the call to warren backend. When fetching the LRS statements, it will
    # get the above mocked statements
    response = await http_client.get(
        url=f"/api/v1/video/{video_id}/views",
        params={
            "since": "2020-01-01T00:00:00+05:00",
            "until": "2020-01-03T23:59:00+05:00",
        },
        headers=auth_headers,
    )

    assert response.status_code == 200

    # Counting all views is expected
    expected_video_views = {
        "total": 4,
        "counts": [
            {"date": "2020-01-01", "count": 3},
            {"date": "2020-01-02", "count": 1},
            {"date": "2020-01-03", "count": 0},
        ],
    }

    assert response.json() == expected_video_views


@pytest.mark.anyio
async def test_unique_views_backend_query(
    http_client: httpx.AsyncClient,
    httpx_mock: HTTPXMock,
    auth_headers: dict,
    db_session,
):
    """Test the video views endpoint, with parameter unique=True."""
    video_id = "uuid://ba4252ce-d042-43b0-92e8-f033f45612ee"
    local_template = VideoPlayedFactory.template
    local_template["object"]["id"] = video_id

    class LocalVideoPlayedFactory(VideoPlayedFactory):
        template: dict = local_template

    def lrs_response(request: httpx.Request):
        """Dynamic mock for the LRS response."""
        statements = [
            json.loads(
                LocalVideoPlayedFactory.build(
                    [
                        {
                            "result": {
                                "extensions": {RESULT_EXTENSION_TIME: view_data["time"]}
                            }
                        },
                        {"timestamp": view_data["timestamp"]},
                    ]
                ).json(),
            )
            for view_data in [
                {"timestamp": "2019-12-31T22:00:00.000+00:00", "time": 3},
                {"timestamp": "2020-01-01T00:00:30.000+00:00", "time": 29},
                {"timestamp": "2020-01-02T00:00:30.000+00:00", "time": 10},
            ]
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

    # Perform the call to warren backend. When fetching the LRS statements, it will
    # get the above mocked statements
    response = await http_client.get(
        url=f"/api/v1/video/{video_id}/views?unique=true",
        params={
            "since": "2020-01-01T00:00:00+02:00",
            "until": "2020-01-03T23:59:00+02:00",
        },
        headers=auth_headers,
    )

    assert response.status_code == 200

    # Counting only the first view is expected
    expected_video_views = {
        "total": 1,
        "counts": [
            {"date": "2020-01-01", "count": 1},
            {"date": "2020-01-02", "count": 0},
            {"date": "2020-01-03", "count": 0},
        ],
    }

    assert response.json() == expected_video_views


@pytest.mark.anyio
@pytest.mark.parametrize(
    "video_id", ["foo", "foo/bar", "/foo/bar", "foo%2Fbar", "%2Ffoo%2Fbar"]
)
async def test_downloads_invalid_video_id(
    http_client: httpx.AsyncClient, auth_headers: dict, video_id: str
):
    """Test the video downloads endpoint with an invalid `video_id` path."""
    date_query_params = {
        "since": "2023-01-01",
        "until": "2023-01-31",
    }

    response = await http_client.get(
        f"/api/v1/video/{video_id}/downloads",
        params=date_query_params,
        headers=auth_headers,
    )

    assert response.status_code == 422
    assert "is not a valid 'IRI'." in response.json().get("detail")[0].get("msg")


@pytest.mark.anyio
async def test_downloads_invalid_auth_headers(http_client: httpx.AsyncClient):
    """Test the video downloads endpoint with an invalid `auth_headers`."""
    response = await http_client.get(
        url="/api/v1/video/uuid://fake-uuid/downloads",
        params={
            "since": "2023-01-01",
            "until": "2023-01-01",
        },
        headers={"Authorization": "Bearer Wrong_Token"},
    )

    assert response.status_code == 401
    assert response.json().get("detail") == "Could not validate credentials"


@pytest.mark.anyio
async def test_downloads_missing_auth_headers(http_client: httpx.AsyncClient):
    """Test the video downloads endpoint with missing `auth_headers`."""
    response = await http_client.get(
        url="/api/v1/video/uuid://fake-uuid/downloads",
        params={
            "since": "2023-01-01",
            "until": "2023-01-01",
        },
    )

    assert response.status_code == 401
    assert response.json().get("detail") == "Not authenticated"


@pytest.mark.anyio
async def test_downloads_valid_video_id_path_but_no_matching_video(
    http_client: httpx.AsyncClient,
    httpx_mock: HTTPXMock,
    auth_headers: dict,
    db_session,
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
        headers=auth_headers,
    )

    assert response.status_code == 200

    # Counting all downloads is expected
    expected_video_downloads = {
        "total": 0,
        "counts": [
            {"date": "2023-01-01", "count": 0},
        ],
    }

    assert response.json() == expected_video_downloads


@pytest.mark.anyio
async def test_downloads_backend_query(
    http_client: httpx.AsyncClient,
    httpx_mock: HTTPXMock,
    auth_headers: dict,
    db_session,
):
    """Test the video downloads endpoint backend query results."""
    video_id = "uuid://ba4252ce-d042-43b0-92e8-f033f45612ee"
    local_template = LMSDownloadedVideoFactory.template
    local_template["object"]["id"] = video_id

    class LocalLMSDownloadedVideoFactory(LMSDownloadedVideoFactory):
        template: dict = local_template

    def lrs_response(request: httpx.Request):
        """Dynamic mock for the LRS response."""
        statements = []
        params = urllib.parse.parse_qs(request.url.query)
        if (
            params.get(b"since")[0] == b"2020-01-01 00:00:00+02:00"
            and params.get(b"until")[0] == b"2020-01-01 23:59:59.999999+02:00"
        ):
            statements = [
                json.loads(
                    LocalLMSDownloadedVideoFactory.build(
                        [
                            {"timestamp": timestamp},
                        ]
                    ).json(),
                )
                for timestamp in [
                    "2019-12-31 23:00:00.000+00:00",
                    "2020-01-01 00:00:00.000+00:00",
                    "2020-01-01 00:00:30.000+00:00",
                ]
            ]
        elif (
            params.get(b"since")[0] == b"2020-01-02 00:00:00+02:00"
            and params.get(b"until")[0] == b"2020-01-02 23:59:59.999999+02:00"
        ):
            statements = [
                json.loads(
                    LocalLMSDownloadedVideoFactory.build(
                        [
                            {"timestamp": "2020-01-02 00:00:00.000+00:00"},
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
    lrs_client.settings.BASE_URL = "http://fake-lrs.com"
    httpx_mock.add_callback(
        callback=lrs_response,
        url=re.compile(r"^http://fake-lrs\.com/xAPI/statements\?.*$"),
        method="GET",
    )

    # Perform the call to warren backend. When fetching the LRS statements, it will
    # get the above mocked statements
    response = await http_client.get(
        url=f"/api/v1/video/{video_id}/downloads",
        params={
            "since": "2020-01-01 00:00:00+02:00",
            "until": "2020-01-03 00:00:00+02:00",
        },
        headers=auth_headers,
    )

    assert response.status_code == 200

    # Counting all downloads is expected
    expected_video_downloads = {
        "total": 4,
        "counts": [
            {"date": "2020-01-01", "count": 3},
            {"date": "2020-01-02", "count": 1},
            {"date": "2020-01-03", "count": 0},
        ],
    }

    assert response.json() == expected_video_downloads


@pytest.mark.anyio
async def test_unique_downloads_backend_query(
    http_client: httpx.AsyncClient,
    httpx_mock: HTTPXMock,
    auth_headers: dict,
    db_session,
):
    """Test the video downloads endpoint, with parameter unique=True."""
    video_id = "uuid://ba4252ce-d042-43b0-92e8-f033f45612ee"

    local_template = LMSDownloadedVideoFactory.template
    local_template["object"]["id"] = video_id

    class LocalLMSDownloadedVideoFactory(LMSDownloadedVideoFactory):
        template: dict = local_template

    def lrs_response(request: httpx.Request):
        """Dynamic mock for the LRS response."""
        statements = [
            json.loads(
                LocalLMSDownloadedVideoFactory.build(
                    [
                        {"timestamp": timestamp},
                    ]
                ).json(),
            )
            for timestamp in [
                "2020-01-01T00:00:00.000+00:00",
                "2020-01-01T00:00:30.000+00:00",
                "2020-01-02T00:00:30.000+00:00",
            ]
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

    # Perform the call to warren backend. When fetching the LRS statements, it will
    # get the above mocked statements
    response = await http_client.get(
        url=f"/api/v1/video/{video_id}/downloads?unique=true",
        params={
            "since": "2020-01-01",
            "until": "2020-01-03",
        },
        headers=auth_headers,
    )

    assert response.status_code == 200

    # Counting only the first download is expected
    expected_video_downloads = {
        "total": 1,
        "counts": [
            {"date": "2020-01-01", "count": 1},
            {"date": "2020-01-02", "count": 0},
            {"date": "2020-01-03", "count": 0},
        ],
    }

    assert response.json() == expected_video_downloads
