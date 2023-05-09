"""Tests for the video API endpoints."""

import pytest

from warren.conf import settings
from warren.factories.video import VideoPlayedFactory


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
async def test_views_backend_query(es_client, http_client):
    """Test the video views endpoint backend query results."""

    await VideoPlayedFactory.save_many(
        es_client,
        [
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
        ],
    )
    await es_client.indices.refresh(index=settings.ES_INDEX)

    response = await http_client.get(
        "/api/v1/video/uuid://ba4252ce-d042-43b0-92e8-f033f45612ee/views?since=2021-12-01T00:00:00.000Z&until=2021-12-01T23:00:00.000Z"
    )
    assert response.status_code == 200
    daily_views = response.json()
    assert daily_views.get("total") == 2
    assert daily_views.get("daily_views") == [{"day": "2021-12-01", "views": 2}]

@pytest.mark.anyio
async def test_views_backend_query_date_in_human_format(es_client, http_client):
    """Test the video views endpoint backend query results."""

    await VideoPlayedFactory.save_many(
        es_client,
        [
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
        ],
    )
    await es_client.indices.refresh(index=settings.ES_INDEX)

    response = await http_client.get(
        "/api/v1/video/uuid://ba4252ce-d042-43b0-92e8-f033f45612ee/views?since=1w&until=3d"
    )
    assert response.status_code == 200
    daily_views = response.json()
    assert daily_views.get("total") == 2
    assert daily_views.get("daily_views") == [{"day": "2021-12-01", "views": 2}]
