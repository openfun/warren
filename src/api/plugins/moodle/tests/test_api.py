"""Tests for the activity API endpoints."""

import json
import re
import urllib

import httpx
import pytest
from pytest_httpx import HTTPXMock
from warren.backends import lrs_client
from warren_moodle.factories import URLViewedFactory


@pytest.mark.anyio
@pytest.mark.parametrize(
    "activity_id", ["foo", "foo/bar", "/foo/bar", "foo%2Fbar", "%2Ffoo%2Fbar"]
)
async def test_views_invalid_activity_id(
    http_client: httpx.AsyncClient, auth_headers: dict, activity_id: str
):
    """Test the activity views endpoint with an invalid `activity_id` path."""
    date_query_params = {
        "since": "2023-01-01",
        "until": "2023-01-31",
    }

    response = await http_client.get(
        f"/api/v1/moodle/{activity_id}/views",
        params=date_query_params,
        headers=auth_headers,
    )

    assert response.status_code == 422
    assert "is not a valid 'IRI'." in response.json().get("detail")[0].get("msg")


@pytest.mark.anyio
async def test_views_valid_activity_id_path_but_no_matching_activity(
    http_client: httpx.AsyncClient,
    httpx_mock: HTTPXMock,
    auth_headers: dict,
    db_session,
):
    """Test the activity views endpoint with a valid `activity_id` but no results."""
    lrs_client.base_url = "http://fake-lrs.com"

    # Mock the call to the LRS so that it would return no statements, as it
    # would do with no matching activity
    httpx_mock.add_response(
        url=re.compile(r"^http://fake-lrs\.com/xAPI/statements\?.*$"),
        method="GET",
        json={"statements": []},
        status_code=200,
    )

    response = await http_client.get(
        url="/api/v1/moodle/uuid://fake-uuid/views",
        params={
            "since": "2023-01-01",
            "until": "2023-01-01",
        },
        headers=auth_headers,
    )

    assert response.status_code == 200

    # Counting all views is expected
    expected_activity_views = {
        "total": 0,
        "counts": [
            {"date": "2023-01-01", "count": 0},
        ],
    }

    assert response.json() == expected_activity_views


@pytest.mark.anyio
async def test_views_invalid_auth_headers(http_client: httpx.AsyncClient):
    """Test the activity views endpoint with an invalid `auth_headers`."""
    response = await http_client.get(
        url="/api/v1/moodle/uuid://fake-uuid/views",
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
    """Test the activity views endpoint with missing `auth_headers`."""
    response = await http_client.get(
        url="/api/v1/moodle/uuid://fake-uuid/views",
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
    """Test the activity views endpoint backend query results."""
    # Define 3 activity views fixtures
    activity_id = "uuid://ba4252ce-d042-43b0-92e8-f033f45612ee"
    local_template = URLViewedFactory.template
    local_template["object"]["id"] = activity_id

    class LocalURLViewedFactory(URLViewedFactory):
        template: dict = local_template

    def lrs_response(request: httpx.Request):
        """Dynamic mock for the LRS response."""
        statements = []
        params = urllib.parse.parse_qs(request.url.query)
        if (
            params.get(b"since")[0] == b"2020-01-01T00:00:00+05:00"
            and params.get(b"until")[0] == b"2020-01-01T23:59:59.999999+05:00"
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
                    {"timestamp": "2019-12-31T20:00:00.000+00:00"},
                    {"timestamp": "2020-01-01T00:00:00.000+00:00"},
                    {"timestamp": "2020-01-01T00:00:30.000+00:00"},
                ]
            ]
        elif (
            params.get(b"since")[0] == b"2020-01-02T00:00:00+05:00"
            and params.get(b"until")[0] == b"2020-01-02T23:59:59.999999+05:00"
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
        url=f"/api/v1/moodle/{activity_id}/views",
        params={
            "since": "2020-01-01T00:00:00+05:00",
            "until": "2020-01-03T23:59:00+05:00",
        },
        headers=auth_headers,
    )

    assert response.status_code == 200

    # Counting all views is expected
    expected_activity_views = {
        "total": 4,
        "counts": [
            {"date": "2020-01-01", "count": 3},
            {"date": "2020-01-02", "count": 1},
            {"date": "2020-01-03", "count": 0},
        ],
    }

    assert response.json() == expected_activity_views


@pytest.mark.anyio
async def test_unique_views_backend_query(
    http_client: httpx.AsyncClient,
    httpx_mock: HTTPXMock,
    auth_headers: dict,
    db_session,
):
    """Test the activity views endpoint, with parameter unique=True."""
    activity_id = "uuid://ba4252ce-d042-43b0-92e8-f033f45612ee"
    local_template = URLViewedFactory.template
    local_template["object"]["id"] = activity_id

    class LocalURLViewedFactory(URLViewedFactory):
        template: dict = local_template

    def lrs_response(request: httpx.Request):
        """Dynamic mock for the LRS response."""
        statements = [
            json.loads(
                LocalURLViewedFactory.build(
                    [
                        {"timestamp": view_data["timestamp"]},
                    ]
                ).json(),
            )
            for view_data in [
                {"timestamp": "2019-12-31T22:00:00.000+00:00"},
                {"timestamp": "2020-01-01T00:00:30.000+00:00"},
                {"timestamp": "2020-01-02T00:00:30.000+00:00"},
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
        url=f"/api/v1/moodle/{activity_id}/views?unique=true",
        params={
            "since": "2020-01-01T00:00:00+02:00",
            "until": "2020-01-03T23:59:00+02:00",
        },
        headers=auth_headers,
    )

    assert response.status_code == 200

    # Counting only the first view is expected
    expected_activity_views = {
        "total": 1,
        "counts": [
            {"date": "2020-01-01", "count": 1},
            {"date": "2020-01-02", "count": 0},
            {"date": "2020-01-03", "count": 0},
        ],
    }

    assert response.json() == expected_activity_views
