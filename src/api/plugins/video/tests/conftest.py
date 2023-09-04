"""Video plugin test fixtures."""

import pytest
from warren.tests.fixtures.app import http_client  # noqa: F401
from warren.tests.fixtures.asynchronous import anyio_backend  # noqa: F401
from warren.tests.fixtures.auth import auth_headers  # noqa: F401


@pytest.fixture
def non_mocked_hosts() -> list:
    """pytest-httpx: let requests to warren pass untouched."""
    return ["localhost"]
