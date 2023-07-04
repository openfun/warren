"""Tests for the video API endpoints."""
import json
from datetime import datetime
from typing import List
from urllib.parse import ParseResult, quote_plus, unquote, urlencode, urlparse

import pytest
from httpx import AsyncClient
from pytest_httpx import HTTPXMock
from ralph.models.xapi import VideoPlayed
from ralph.models.xapi.concepts.verbs.video import PlayedVerb
from warren.backends import lrs_client
from warren.filters import DatetimeRange
from warren.models import Response
from warren_video.models import VideoViews


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
    http_client: AsyncClient, httpx_mock: HTTPXMock, video_id
):
    """Test the video views endpoint with a valid "video_id" but no results."""
    date_range = DatetimeRange()

    base_url = "http://fake-lrs.com"
    lrs_client.base_url = base_url

    params = {
        "since": date_range.since.astimezone().isoformat(),
        "until": date_range.until.astimezone().isoformat(),
    }

    query_string = (
        f"verb={quote_plus(PlayedVerb().id, safe='/')}&activity="
        f"{quote_plus(unquote(video_id), safe='/')}"
    )

    lrs_url = ParseResult(
        scheme=urlparse(lrs_client.base_url).scheme,
        netloc=urlparse(lrs_client.base_url).netloc,
        path=lrs_client.statements_endpoint,
        query=f"{query_string}&{urlencode({**params, 'limit': 500})}",
        params="",
        fragment="",
    ).geturl()

    httpx_mock.add_response(
        url=lrs_url, method="GET", json={"statements": []}, status_code=200
    )

    response = await http_client.get(f"/api/v1/video/{video_id}/views", params=params)
    no_statement_response = VideoViews(
        total_views=0,
        views_count_by_date=[],
    )

    assert response.status_code == 200
    assert VideoViews.parse_obj(response.json()) == no_statement_response


@pytest.mark.anyio
async def test_views_backend_query(
    http_client: AsyncClient,
    httpx_mock: HTTPXMock,
    video_statements: List[VideoPlayed],
):
    """Test the video views endpoint backend query results."""
    video_id = "uuid://ba4252ce-d042-43b0-92e8-f033f45612ee"

    date_range = DatetimeRange()

    base_url = "http://fake-lrs.com"
    lrs_client.base_url = base_url

    params = {
        "since": date_range.since.astimezone().isoformat(),
        "until": date_range.until.astimezone().isoformat(),
    }

    query_string = (
        f"verb={quote_plus(PlayedVerb().id, safe='/')}&activity="
        f"{quote_plus(unquote(video_id), safe='/')}"
    )

    lrs_url = ParseResult(
        scheme=urlparse(lrs_client.base_url).scheme,
        netloc=urlparse(lrs_client.base_url).netloc,
        path=lrs_client.statements_endpoint,
        query=f"{query_string}&{urlencode({**params, 'limit': 500})}",
        params="",
        fragment="",
    ).geturl()

    statements = [json.loads(statement.json()) for statement in video_statements]
    httpx_mock.add_response(
        url=lrs_url, method="GET", json={"statements": statements}, status_code=200
    )

    response = await http_client.get(f"/api/v1/video/{video_id}/views", params=params)

    assert response.status_code == 200

    video_views = (Response[VideoViews]).parse_obj(response.json()).content

    assert video_views["total_views"] == 1
    assert video_views["count_by_date"][0] == {
        "date": datetime.utcnow().date().isoformat(),
        "count": 1,
    }
