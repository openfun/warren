"""Tests for the video API endpoints."""

import arrow
import pytest
from warren_video.api import VideoDayViews, VideoViews

from warren.conf import settings
from warren.factories.video import VideoPlayedFactory
from warren.filters import DatetimeRange


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
    video_id, es_client, http_client
):
    """Test the video views endpoint with a valid "video_id" but no results."""

    default_range = DatetimeRange()
    no_statements_response = VideoViews(
        total=0,
        daily_views=[
            VideoDayViews(day=day.format("YYYY-MM-DD"))
            for day in arrow.Arrow.range(
                "day", default_range.since, default_range.until
            )
        ],
    )

    response = await http_client.get(f"/api/v1/video/{video_id}/views")
    assert response.status_code == 200
    assert VideoViews.parse_obj(response.json()) == no_statements_response


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
                    {"timestamp": "2023-02-03T15:34:00.000-01:00"},
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
                    {"timestamp": "2023-02-07T19:34:00.000-01:00"},
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
                    {"timestamp": "2023-02-07T15:28:00.000-01:00"},
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
        "/api/v1/video/uuid://ba4252ce-d042-43b0-92e8-f033f45612ee/views",
        params={"since": "2023-02-01", "until": "2023-02-10"},
    )
    assert response.status_code == 200
    video_views = VideoViews.parse_obj(response.json())
    assert video_views.total == 2
    assert video_views.daily_views == [
        VideoDayViews(day="2023-02-01", views=0),
        VideoDayViews(day="2023-02-02", views=0),
        VideoDayViews(day="2023-02-03", views=1),
        VideoDayViews(day="2023-02-04", views=0),
        VideoDayViews(day="2023-02-05", views=0),
        VideoDayViews(day="2023-02-06", views=0),
        VideoDayViews(day="2023-02-07", views=1),
        VideoDayViews(day="2023-02-08", views=0),
        VideoDayViews(day="2023-02-09", views=0),
        VideoDayViews(day="2023-02-10", views=0),
    ]
