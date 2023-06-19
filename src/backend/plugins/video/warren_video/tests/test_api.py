"""Tests for the video API endpoints."""

import pytest
from httpx import AsyncClient

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
async def test_views_invalid_video_id_path(
    http_client: AsyncClient, video_id: str, parsed_video_id: str
):
    """Test the video views endpoint with an invalid "video_id" path."""
    date_range = DatetimeRange()
    params = {
        "since": date_range.since.astimezone().isoformat(),
        "until": date_range.until.astimezone().isoformat(),
    }

    response = await http_client.get(f"/api/v1/video/{video_id}/views", params=params)

    assert response.status_code == 422
    assert (
        response.json().get("detail")[0].get("msg")
        == f"'{parsed_video_id}' is not a valid 'IRI'."
    )
