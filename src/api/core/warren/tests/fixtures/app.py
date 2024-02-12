"""Fixtures for the core warren app."""

from typing import AsyncIterator

import pytest
from httpx import AsyncClient

from warren.api import app
from warren.conf import settings
from warren.utils import forge_lti_token


@pytest.fixture
@pytest.mark.anyio
async def http_client() -> AsyncIterator[AsyncClient]:
    """Handle application lifespan while yielding asynchronous HTTP client."""
    async with AsyncClient(app=app, base_url=settings.SERVER_URL) as client:
        yield client


@pytest.fixture
@pytest.mark.anyio
async def http_auth_client() -> AsyncIterator[AsyncClient]:
    """Handle application lifespan while yielding asynchronous auth HTTP client.

    In this case, the client is supposed to be authenticated via LTI.
    """
    async with AsyncClient(
        app=app,
        base_url=settings.SERVER_URL,
        headers={"Authorization": f"Bearer {forge_lti_token()}"},
    ) as client:
        yield client
