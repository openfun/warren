"""Tests for the viewers indicator."""

import json

import arrow
import pytest
from ralph.models.xapi.concepts.verbs.video import PlayedVerb
from warren.backends import lrs_client
from warren.filters import DatetimeRange
from warren_video.metric.count import Count
from warren_video.tests.conftest import FAKE_VIDEO_IDS
from warren_video.tests.factories import VideoPlayedFactory
from warren_video.tests.fixtures import create_lrs_url


@pytest.mark.anyio
@pytest.mark.parametrize("video_id", FAKE_VIDEO_IDS)
async def test_no_matching_video(http_client, httpx_mock, video_id):
    """Test the video viewers endpoint with a valid "video_id" but no results."""
    date_range = DatetimeRange()

    httpx_mock.add_response(
        url=create_lrs_url(
            base_url="http://fake-lrs.com",
            video_id=video_id,
            verb=PlayedVerb(),
            date_range=date_range,
        ),
        method="GET",
        json={"statements": []},
        status_code=200,
    )

    params = {
        "since": date_range.since.astimezone().isoformat(),
        "until": date_range.until.astimezone().isoformat(),
    }

    lrs_client.base_url = "http://fake-lrs.com"
    response = await http_client.get(f"/api/v1/video/{video_id}/viewers", params=params)
    assert response.status_code == 200

    assert Count.parse_obj(response.json()) == Count(total=0)


@pytest.mark.anyio
async def test_matching_videos(http_client, httpx_mock):
    """Test the video viewers endpoint backend query results."""
    date_range = DatetimeRange()
    video_id = "uuid://ba4252ce-d042-43b0-92e8-f033f45612ee"

    video_statements = [
        json.loads(
            VideoPlayedFactory.build(
                [
                    {"object": {"id": video_id}},
                    {
                        "result": {
                            "extensions": {
                                "https://w3id.org/xapi/video/extensions/time": time
                            }
                        }
                    },
                    {
                        "actor": {
                            "objectType": "Agent",
                            "account": {
                                "name": actor_account_name,
                                "homePage": "http://lms.example.org",
                            },
                        },
                    },
                    {"timestamp": arrow.utcnow().isoformat()},
                ]
            ).json()
        )
        for time, actor_account_name in (
            (0, "test"),
            (10, "other"),
            (20, "another"),
            (100, "test"),
        )
    ]

    lrs_client.base_url = "http://fake-lrs.com"

    httpx_mock.add_response(
        url=create_lrs_url(
            base_url="http://fake-lrs.com",
            video_id=video_id,
            verb=PlayedVerb(),
            date_range=date_range,
        ),
        method="GET",
        json={"statements": video_statements},
        status_code=200,
    )

    params = {
        "since": date_range.since.astimezone().isoformat(),
        "until": date_range.until.astimezone().isoformat(),
    }
    response = await http_client.get(f"/api/v1/video/{video_id}/viewers", params=params)
    assert response.status_code == 200

    assert Count.parse_obj(response.json()) == Count(total=3)
