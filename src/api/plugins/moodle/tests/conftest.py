"""Video plugin test fixtures."""

# ruff: noqa: F401

import pytest
from warren.tests.fixtures.app import http_client
from warren.tests.fixtures.asynchronous import anyio_backend
from warren.tests.fixtures.auth import auth_headers
from warren.tests.fixtures.db import (
    db_engine,
    db_session,
    force_db_test_session,
)


@pytest.fixture
def non_mocked_hosts() -> list:
    """pytest-httpx: let requests to warren pass untouched."""
    return ["localhost"]
