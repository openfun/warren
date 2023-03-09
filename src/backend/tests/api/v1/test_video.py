"""Tests for the video API endpoints."""

import pytest
from httpx import AsyncClient

from warren.api import app
from warren.conf import settings


@pytest.mark.asyncio
async def test_views_video_id_path(es):
    """Test the video views endpoint "video_id" path validity."""

    async with AsyncClient(app=app, base_url=settings.SERVER_URL) as client:
        response = await client.get("/api/v1/video/foo/views")
    assert response.status_code == 422
    assert response.json().get("detail")[0].get("msg") == "'foo' is not a valid 'IRI'."

    async with AsyncClient(app=app, base_url=settings.SERVER_URL) as client:
        response = await client.get("/api/v1/video/foo/bar/views")
    assert response.status_code == 422
    assert (
        response.json().get("detail")[0].get("msg") == "'foo/bar' is not a valid 'IRI'."
    )

    async with AsyncClient(app=app, base_url=settings.SERVER_URL) as client:
        response = await client.get("/api/v1/video//foo/bar/views")
    assert response.status_code == 422
    assert (
        response.json().get("detail")[0].get("msg")
        == "'/foo/bar' is not a valid 'IRI'."
    )

    async with AsyncClient(app=app, base_url=settings.SERVER_URL) as client:
        response = await client.get("/api/v1/video/foo%2Fbar/views")
    assert response.status_code == 422
    assert (
        response.json().get("detail")[0].get("msg") == "'foo/bar' is not a valid 'IRI'."
    )

    async with AsyncClient(app=app, base_url=settings.SERVER_URL) as client:
        response = await client.get("/api/v1/video/%2Ffoo%2Fbar/views")
    assert response.status_code == 422
    assert (
        response.json().get("detail")[0].get("msg")
        == "'/foo/bar' is not a valid 'IRI'."
    )

    no_statements_response = {"daily_views": [], "total": 0}

    async with AsyncClient(app=app, base_url=settings.SERVER_URL) as client:
        response = await client.get("/api/v1/video/http://foo/bar/views")
    assert response.status_code == 200
    assert response.json() == no_statements_response

    async with AsyncClient(app=app, base_url=settings.SERVER_URL) as client:
        response = await client.get("/api/v1/video/http%3A%2F%2Ffoo%2Fbar/views")
    assert response.status_code == 200
    assert response.json() == no_statements_response

    async with AsyncClient(app=app, base_url=settings.SERVER_URL) as client:
        response = await client.get("/api/v1/video/uuid://foo/bar/views")
    assert response.status_code == 200
    assert response.json() == no_statements_response

    async with AsyncClient(app=app, base_url=settings.SERVER_URL) as client:
        response = await client.get("/api/v1/video/uuid%3A%2F%2Ffoo%2Fbar/views")
    assert response.status_code == 200
    assert response.json() == no_statements_response
