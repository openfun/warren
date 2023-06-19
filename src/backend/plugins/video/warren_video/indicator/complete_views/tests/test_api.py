"""Tests for the complete views indicator."""
import json

import arrow
import pytest
from ralph.models.xapi.concepts.verbs.scorm_profile import CompletedVerb
from warren_video.metric.daytimeseries import DayTimeSeries, DayTimeSeriesDataPoint
from warren_video.tests.conftest import FAKE_VIDEO_IDS, core_settings
from warren_video.tests.factories import VideoCompletedFactory
from warren_video.tests.fixtures import create_lrs_url

from warren.backends import lrs_client
from warren.filters import DatetimeRange


@pytest.mark.anyio
@pytest.mark.parametrize("video_id", FAKE_VIDEO_IDS)
async def test_no_matching_video(http_client, httpx_mock, video_id):
    """Test the video complete views endpoint with a valid "video_id" but no results."""
    date_range = DatetimeRange()

    httpx_mock.add_response(
        url=create_lrs_url(
            base_url="http://fake-lrs.com",
            video_id=video_id,
            verb=CompletedVerb(),
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
    response = await http_client.get(
        f"/api/v1/video/{video_id}/complete_views", params=params
    )
    assert response.status_code == 200

    assert DayTimeSeries.parse_obj(response.json()) == DayTimeSeries(
        day_totals=[
            DayTimeSeriesDataPoint(day=day.format(core_settings.DATE_FORMAT))
            for day in arrow.Arrow.range("day", date_range.since, date_range.until)
        ]
    )


@pytest.mark.anyio
async def test_matching_videos(http_client, httpx_mock):
    """Test the video complete views endpoint backend query results."""
    date_range = DatetimeRange()
    video_id = "uuid://ba4252ce-d042-43b0-92e8-f033f45612ee"
    expected_res = DayTimeSeries(
        day_totals=[
            DayTimeSeriesDataPoint(day=day.format(core_settings.DATE_FORMAT))
            for day in arrow.Arrow.range("day", date_range.since, date_range.until)
        ]
    )
    expected_res.day_totals[-1].total = 3
    expected_res.total = 3

    video_statements = [
        json.loads(
            VideoCompletedFactory.build(
                [
                    {"object": {"id": video_id}},
                    {"timestamp": arrow.utcnow().isoformat()},
                ]
            ).json()
        )
        for _ in range(3)
    ]

    lrs_client.base_url = "http://fake-lrs.com"

    httpx_mock.add_response(
        url=create_lrs_url(
            base_url="http://fake-lrs.com",
            video_id=video_id,
            verb=CompletedVerb(),
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
    response = await http_client.get(
        f"/api/v1/video/{video_id}/complete_views", params=params
    )
    assert response.status_code == 200

    assert DayTimeSeries.parse_obj(response.json()) == expected_res
