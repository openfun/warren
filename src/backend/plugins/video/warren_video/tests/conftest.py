"""Video plugin main fixtures."""

# pylint: disable=unused-import
import json

# pylint: disable=unused-import
from typing import List

import pytest
from arrow import arrow
from httpx import Response
from pydantic import BaseModel
from warren_video.indicator.indicator import VideoIndicator
from warren_video.metric.count import Count
from warren_video.metric.histogram import Histogram, HistogramDay
from warren_video.tests.fixtures import (
    VideoStatementParams,
    make_video_statements,
    mock_video_lrs_request,
)

from warren.conf import Settings
from warren.filters import DatetimeRange
from warren.tests.fixtures.asynchronous import anyio_backend  # noqa: F401

core_settings = Settings()


@pytest.fixture
def non_mocked_hosts() -> list:
    """pytest-httpx: let requests to warren pass untouched."""
    return ["localhost"]


def create_empty_stat(
    indicator: VideoIndicator, date_range: DatetimeRange
) -> BaseModel:
    """Create an empty response stat object for the given indicator."""
    if indicator.return_type == Histogram:
        return Histogram(
            day_totals=[
                HistogramDay(day=day.format(core_settings.DATE_FORMAT))
                for day in arrow.Arrow.range("day", date_range.since, date_range.until)
            ]
        )
    if indicator.return_type == Count:
        return Count(total=0)

    raise NotImplementedError(f"Unknown metric {indicator.metric}")


async def get_video_indicator_result(
    client, video_id: str, indicator_name: str, date_range: DatetimeRange
) -> Response:
    """Execute an http request to the video views endpoint."""
    params = {
        "since": date_range.since.astimezone().isoformat(),
        "until": date_range.until.astimezone().isoformat(),
    }

    return await client.get(f"/api/v1/video/{video_id}/{indicator_name}", params=params)


@pytest.fixture
def assert_no_matching_video(httpx_mock, http_client):
    """Test the video endpoint with a valid "video_id" but no results."""

    async def execute_test(indicator: VideoIndicator, video_id: str):
        """Assert the given request to the given indicator returns the right results."""

        date_range = DatetimeRange()

        mock_video_lrs_request(
            httpx_mock, video_id, indicator.verb, date_range, statements=[]
        )

        response = await get_video_indicator_result(
            http_client, video_id, indicator.name, date_range
        )

        assert response.status_code == 200

        assert indicator.return_type.parse_obj(response.json()) == create_empty_stat(
            indicator, date_range
        )

    return execute_test


@pytest.fixture
def assert_matching_videos(httpx_mock, http_client):
    """Test the video endpoint with a valid "video_id" and results."""
    # pylint: disable=redefined-outer-name

    async def execute_test(
        test_data: List[VideoStatementParams],
        indicator: VideoIndicator,
        video_id: str,
        expected_res: BaseModel,
        date_range=DatetimeRange(),
    ):
        """Test the video complete views endpoint backend query results."""

        video_statements = make_video_statements(test_data, indicator.verb)

        lrs_response = [json.loads(statement.json()) for statement in video_statements]
        mock_video_lrs_request(
            httpx_mock, video_id, indicator.verb, date_range, lrs_response
        )

        response = await get_video_indicator_result(
            http_client, video_id, indicator.name, date_range
        )

        assert response.status_code == 200

        assert indicator.return_type.parse_obj(response.json()) == expected_res

    return execute_test


FAKE_VIDEO_IDS = [
    "http://foo/bar",
    "http%3A%2F%2Ffoo%2Fbar",
    "uuid://foo/bar",
    "uuid%3A%2F%2Ffoo%2Fbar",
]
