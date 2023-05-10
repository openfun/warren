"""Tests for the video API endpoints."""

import pytest

from warren.conf import settings
from warren.factories.video import VideoPlayedFactory


@pytest.fixture
async def video_played_data():
    return [
        VideoPlayedFactory.build(
            [
                {"object": {"id": "uuid://ba4252ce-d042-43b0-92e8-f033f45612ee"}},
                {
                    "result": {
                        "extensions": {
                            "https://w3id.org/xapi/video/extensions/time": 0.3
                        }
                    }
                },
            ]
        ),
        VideoPlayedFactory.build(
            [
                {"object": {"id": "uuid://ba4252ce-d042-43b0-92e8-f033f45612ee"}},
                {
                    "result": {
                        "extensions": {
                            "https://w3id.org/xapi/video/extensions/time": 12.4
                        }
                    }
                },
            ]
        ),
        VideoPlayedFactory.build(
            [
                {"object": {"id": "uuid://ba4252ce-d042-43b0-92e8-f033f45612ee"}},
                {
                    "result": {
                        "extensions": {
                            "https://w3id.org/xapi/video/extensions/time": 33.1
                        }
                    }
                },
            ]
        ),
        VideoPlayedFactory.build(
            [
                {"object": {"id": "uuid://8efd1802-dce0-4e81-88e4-39760e683fd8"}},
            ]
        ),
    ]


@pytest.mark.anyio
@pytest.mark.parametrize(
    "video_id,parsed_video_id",
    [
        ("foo", "foo"),
        ("foo/bar", "foo/bar"),
        ("/foo/bar", "/foo/bar"),
        ("foo%2Fbar", "foo/bar"),
        ("%2Ffoo%2Fbar", "/foo/bar"),
    ],
)
async def test_views_invalid_video_id_path(video_id, parsed_video_id, http_client):
    """Test the video views endpoint with an invalid "video_id" path."""
    response = await http_client.get(f"/api/v1/video/{video_id}/views")
    assert response.status_code == 422
    assert (
        response.json().get("detail")[0].get("msg")
        == f"'{parsed_video_id}' is not a valid 'IRI'."
    )


# pylint: disable=unused-argument
@pytest.mark.anyio
@pytest.mark.parametrize(
    "video_id",
    [
        "http://foo/bar",
        "http%3A%2F%2Ffoo%2Fbar",
        "uuid://foo/bar",
        "uuid%3A%2F%2Ffoo%2Fbar",
    ],
)
async def test_views_valid_video_id_path_but_no_matching_video(
    video_id, es_client, http_client, last_week_views
):
    """Test the video views endpoint with a valid "video_id" but no results."""

    empty_week = last_week_views()

    response = await http_client.get(f"/api/v1/video/{video_id}/views")
    assert response.status_code == 200
    assert response.json()["total"] == 0
    assert len(response.json()["daily_views"]) == 8
    assert response.json()["daily_views"] == empty_week


@pytest.mark.anyio
async def test_views_backend_query(es_client, http_client, video_played_data):
    """Test the video views endpoint backend query results."""

    await VideoPlayedFactory.save_many(es_client, video_played_data)

    await es_client.indices.refresh(index=settings.ES_INDEX)

    response = await http_client.get(
        "/api/v1/video/uuid://ba4252ce-d042-43b0-92e8-f033f45612ee/views?since=2021-12-01T00:00:00.000Z&until=2021-12-01T23:00:00.000Z"
    )
    assert response.status_code == 200
    daily_views = response.json()
    assert daily_views.get("total") == 2
    assert daily_views.get("daily_views") == [{"day": "2021-12-01", "views": 2}]


@pytest.mark.anyio
async def test_views_backend_query_date_in_human_format(
    es_client, http_client, last_week_views, video_played_data
):
    """Test the video views endpoint backend query results."""

    await VideoPlayedFactory.save_many(es_client, video_played_data)

    await es_client.indices.refresh(index=settings.ES_INDEX)

    response_1w_3d = await http_client.get(
        "/api/v1/video/uuid://ba4252ce-d042-43b0-92e8-f033f45612ee/views?since=1w&until=3d"
    )

    assert response_1w_3d.status_code == 200
    daily_views = response_1w_3d.json()
    assert daily_views.get("total") == 0
    assert daily_views.get("daily_views") == last_week_views()[:4]


@pytest.mark.anyio
async def test_views_backend_query_return_error400_if_until_older_than_since(
    http_client,
):
    """Test if error 400 is returned when 'until' date is older than 'since' date"""

    response = await http_client.get(
        f"/api/v1/video/uuid://ba4252ce-d042-43b0-92e8-f033f45612ee/views?since=2021-12-01T00:00:00.000Z&until=2021-11-01T23:00:00.000Z"
    )
    assert response.status_code == 400
    assert "Invalid time range" in response.json().get("detail")


@pytest.mark.anyio
@pytest.mark.parametrize(
    "bad_since",
    ["abc", "d3", ""],
)
@pytest.mark.parametrize(
    "bad_until",
    ["abc", "d3", ""],
)
async def test_views_backend_query_return_error400_if_unparsable_date_param(
    http_client, bad_until, bad_since
):
    """Test if error 400 is returned when we give unparsable date params"""

    response = await http_client.get(
        f"/api/v1/video/uuid://ba4252ce-d042-43b0-92e8-f033f45612ee/views?since={bad_since}&until={bad_until}"
    )
    assert response.status_code == 400
    assert "Date parsing error" in response.json().get("detail")


@pytest.mark.anyio
@pytest.mark.parametrize(
    "params,nb_days",
    [
        ("?since=4days", 5),  # 4 days until now
        ("?until=3days", 4),  # last week + 3 days
    ],
)
async def test_views_calling_with_only_one_param(
    params, nb_days, es_client, http_client, video_played_data
):
    """Test the video views endpoint with only one param, expect the backend to use the default for the other param"""

    await VideoPlayedFactory.save_many(es_client, video_played_data)
    response = await http_client.get(
        f"/api/v1/video/uuid://ba4252ce-d042-43b0-92e8-f033f45612ee/views{params}"
    )
    assert response.status_code == 200
    assert len(response.json().get("daily_views")) == nb_days
