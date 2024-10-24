"""Tests for the activity API endpoints."""

import re
from unittest.mock import patch

import httpx
import pytest
from pytest_httpx import HTTPXMock
from warren.backends import lrs_client
from warren.models import DailyCounts, DailyUniqueCount, DailyUniqueCounts
from warren.utils import forge_lti_token
from warren_moodle.indicators import (
    CourseDailyUniqueViews,
    CourseDailyViews,
    DailyUniqueViews,
    DailyViews,
)


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
    activity_id = "uuid://fake-uuid"

    # Mock the call to the LRS so that it would return no statements, as it
    # would do with no matching activity
    httpx_mock.add_response(
        url=re.compile(r"^http://fake-lrs\.com/xAPI/statements\?.*$"),
        method="GET",
        json={"statements": []},
        status_code=200,
    )

    response = await http_client.get(
        url=f"/api/v1/moodle/{activity_id}/views",
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
    activity_id = "uuid://c16e5e8e-d0c3-47a8-81b6-0d8fb971d2e0"

    response = await http_client.get(
        url=f"/api/v1/moodle/{activity_id}/views",
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
    activity_id = "uuid://c16e5e8e-d0c3-47a8-81b6-0d8fb971d2e0"

    response = await http_client.get(
        url=f"/api/v1/moodle/{activity_id}/views",
        params={
            "since": "2023-01-01",
            "until": "2023-01-01",
        },
    )

    assert response.status_code == 401
    assert response.json().get("detail") == "Not authenticated"


@pytest.mark.anyio
async def test_views_daily_views(http_client: httpx.AsyncClient, auth_headers: dict):
    """Test the activity views endpoint for daily views."""
    activity_id = "uuid://c16e5e8e-d0c3-47a8-81b6-0d8fb971d2e0"

    # Create a mock return value for the `get_or_compute` method
    mock_daily_counts = DailyCounts(
        total=1, counts=[{"date": "2023-01-01", "count": 1}]
    )

    # Patch `DailyViews.get_or_compute` to return the mock result
    with patch.object(
        DailyViews, "get_or_compute", return_value=mock_daily_counts
    ) as mock_get_or_compute:
        response = await http_client.get(
            f"/api/v1/moodle/{activity_id}/views",
            params={"since": "2023-01-01", "until": "2023-01-31", "unique": "false"},
            headers=auth_headers,
        )

    assert response.status_code == 200
    assert response.json() == {
        "total": 1,  # The mocked total views count
        "counts": [
            {"date": "2023-01-01", "count": 1},
        ],
    }

    # Ensure the method was called correctly
    mock_get_or_compute.assert_called_once()


@pytest.mark.anyio
async def test_views_daily_unique_views(
    http_client: httpx.AsyncClient, auth_headers: dict
):
    """Test the activity views endpoint for daily unique views."""
    activity_id = "uuid://c16e5e8e-d0c3-47a8-81b6-0d8fb971d2e0"

    # Create a mock return value for the `get_or_compute` method
    mock_daily_unique_counts = {
        "total": 1,
        "counts": [
            DailyUniqueCount(date="2023-01-01", count=1, users={"john_doe"}),
            DailyUniqueCount(date="2023-01-02", count=0, users=set()),
            DailyUniqueCount(date="2023-01-03", count=0, users=set()),
        ],
    }

    # Patch `DailyViews.get_or_compute` to return the mock result
    with patch.object(
        DailyUniqueViews, "get_or_compute", return_value=mock_daily_unique_counts
    ) as mock_get_or_compute:
        response = await http_client.get(
            f"/api/v1/moodle/{activity_id}/views",
            params={"since": "2023-01-01", "until": "2023-01-03", "unique": "true"},
            headers=auth_headers,
        )

    assert response.status_code == 200
    assert response.json() == {
        "total": 1,  # The mocked total views count
        "counts": [
            {"date": "2023-01-01", "count": 1},
            {"date": "2023-01-02", "count": 0},
            {"date": "2023-01-03", "count": 0},
        ],
    }

    # Ensure the method was called correctly
    mock_get_or_compute.assert_called_once()


@pytest.mark.anyio
async def test_course_views_invalid_auth_headers(http_client: httpx.AsyncClient):
    """Test the course views endpoint with an invalid `auth_headers`."""
    course_id = "uuid://c16e5e8e-d0c3-47a8-81b6-0d8fb971d2e0"

    response = await http_client.get(
        url=f"/api/v1/moodle/{course_id}/views",
        params={
            "since": "2023-01-01",
            "until": "2023-01-01",
        },
        headers={"Authorization": "Bearer Wrong_Token"},
    )

    assert response.status_code == 401
    assert response.json().get("detail") == "Could not validate credentials"


@pytest.mark.anyio
async def test_course_views_missing_auth_headers(http_client: httpx.AsyncClient):
    """Test the course views endpoint with missing `auth_headers`."""
    course_id = "uuid://c16e5e8e-d0c3-47a8-81b6-0d8fb971d2e0"

    response = await http_client.get(
        url=f"/api/v1/moodle/{course_id}/views",
        params={
            "since": "2023-01-01",
            "until": "2023-01-01",
        },
    )

    assert response.status_code == 401
    assert response.json().get("detail") == "Not authenticated"


@pytest.mark.anyio
async def test_course_views_daily_views_with_no_modname(
    http_client: httpx.AsyncClient, auth_headers: dict
):
    """Test the course views endpoint for daily views with no `modname` filter."""
    token = forge_lti_token(course_id="uuid://c16e5e8e-d0c3-47a8-81b6-0d8fb971d2e0")

    # Create a mock return value for the `get_or_compute` method
    mock_course_daily_counts = [
        {
            "id": "activity1",
            "modname": "mod_forum",
            "views": DailyCounts(total=1, counts=[{"date": "2023-01-01", "count": 1}]),
        }
    ]
    # Patch `DailyViews.get_or_compute` to return the mock result
    with patch.object(
        CourseDailyViews, "get_or_compute", return_value=mock_course_daily_counts
    ) as mock_get_or_compute:
        response = await http_client.get(
            "/api/v1/moodle/views",
            params={"since": "2023-01-01", "until": "2023-01-03", "unique": "false"},
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": "activity1",
            "modname": "mod_forum",
            "views": {
                "total": 1,  # The mocked total views count
                "counts": [
                    {"date": "2023-01-01", "count": 1},
                ],
            },
        }
    ]

    # Ensure the method was called correctly
    mock_get_or_compute.assert_called_once()


@pytest.mark.anyio
async def test_course_views_daily_views_with_modname(
    http_client: httpx.AsyncClient, auth_headers: dict
):
    """Test the course views endpoint for daily views with `modname` filter."""
    token = forge_lti_token(course_id="uuid://c16e5e8e-d0c3-47a8-81b6-0d8fb971d2e0")

    # Create a mock return value for the `get_or_compute` method
    mock_course_daily_counts = [
        {
            "id": "activity1",
            "modname": "mod_forum",
            "views": DailyCounts(total=1, counts=[{"date": "2023-01-01", "count": 1}]),
        },
        {
            "id": "activity2",
            "modname": "mod_chat",
            "views": DailyCounts(total=1, counts=[{"date": "2023-01-02", "count": 12}]),
        },
    ]

    # Patch `DailyViews.get_or_compute` to return the mock result
    with patch.object(
        CourseDailyViews, "get_or_compute", return_value=mock_course_daily_counts
    ) as mock_get_or_compute:
        response = await http_client.get(
            "/api/v1/moodle/views",
            params={
                "since": "2023-01-01",
                "until": "2023-01-03",
                "unique": "false",
                "modname": ["mod_chat", "mod_forum"],
            },
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": "activity1",
            "modname": "mod_forum",
            "views": {"total": 1, "counts": [{"date": "2023-01-01", "count": 1}]},
        },
        {
            "id": "activity2",
            "modname": "mod_chat",
            "views": {"total": 1, "counts": [{"date": "2023-01-02", "count": 12}]},
        },
    ]

    # Ensure the method was called correctly
    mock_get_or_compute.assert_called_once()


@pytest.mark.anyio
async def test_course_views_daily_unique_views_with_no_modname(
    http_client: httpx.AsyncClient, auth_headers: dict
):
    """Test the course views endpoint for daily unique views with no `modname`
    filter.
    """  # noqa: D205
    token = forge_lti_token(course_id="uuid://c16e5e8e-d0c3-47a8-81b6-0d8fb971d2e0")

    # Create a mock return value for the `get_or_compute` method
    mock_course_daily_unique_counts = [
        {
            "id": "activity1",
            "modname": "mod_forum",
            "unique_views": DailyUniqueCounts(
                total=1, counts=[{"date": "2023-01-01", "count": 1}]
            ),
        }
    ]

    # Patch `DailyViews.get_or_compute` to return the mock result
    with patch.object(
        CourseDailyUniqueViews,
        "get_or_compute",
        return_value=mock_course_daily_unique_counts,
    ) as mock_get_or_compute:
        response = await http_client.get(
            "/api/v1/moodle/views",
            params={"since": "2023-01-01", "until": "2023-01-03", "unique": "true"},
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": "activity1",
            "modname": "mod_forum",
            "unique_views": {
                "total": 1,
                "counts": [{"date": "2023-01-01", "count": 1, "users": []}],
            },
        }
    ]

    # Ensure the method was called correctly
    mock_get_or_compute.assert_called_once()


@pytest.mark.anyio
async def test_course_views_daily_unique_views_with_modname(
    http_client: httpx.AsyncClient, auth_headers: dict
):
    """Test the course views endpoint for daily unique views with modname filter."""
    token = forge_lti_token(course_id="uuid://c16e5e8e-d0c3-47a8-81b6-0d8fb971d2e0")

    # Create a mock return value for the `get_or_compute` method
    mock_course_daily_unique_counts = [
        {
            "id": "activity1",
            "modname": "mod_forum",
            "views": DailyUniqueCounts(
                total=1, counts=[{"date": "2023-01-01", "count": 1}]
            ),
        },
        {
            "id": "activity2",
            "modname": "mod_chat",
            "unique_views": DailyUniqueCounts(
                total=1, counts=[{"date": "2023-01-02", "count": 12}]
            ),
        },
    ]

    # Patch `DailyViews.get_or_compute` to return the mock result
    with patch.object(
        CourseDailyUniqueViews,
        "get_or_compute",
        return_value=mock_course_daily_unique_counts,
    ) as mock_get_or_compute:
        response = await http_client.get(
            "/api/v1/moodle/views",
            params={
                "since": "2023-01-01",
                "until": "2023-01-31",
                "unique": "true",
                "modname": ["mod_chat", "mod_forum"],
            },
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": "activity1",
            "modname": "mod_forum",
            "views": {
                "total": 1,
                "counts": [{"date": "2023-01-01", "count": 1, "users": []}],
            },
        },
        {
            "id": "activity2",
            "modname": "mod_chat",
            "unique_views": {
                "total": 1,
                "counts": [{"date": "2023-01-02", "count": 12, "users": []}],
            },
        },
    ]

    # Ensure the method was called correctly
    mock_get_or_compute.assert_called_once()
