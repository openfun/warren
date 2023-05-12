"""Async test fixtures."""

import pytest


@pytest.fixture
def anyio_backend():
    """Use asyncio as the only default backend."""
    return "asyncio"
