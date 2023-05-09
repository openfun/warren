"""Module py.test fixtures."""

# pylint: disable=unused-import

import pytest

from .fixtures.app import http_client  # noqa: F401
from .fixtures.backends import es_client, no_cached_es_client  # noqa: F401
from .fixtures.time import last_week_views

@pytest.fixture
def anyio_backend():
    """Use asyncio as the only default backend."""
    return "asyncio"
