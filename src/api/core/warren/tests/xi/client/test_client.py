"""Tests for XI experiences client."""

import pytest

from warren.xi.client import ExperienceIndex


@pytest.mark.anyio
async def test_xi_client():
    """A high level test for the XI client."""
    client = ExperienceIndex(url="https://xi.fake.com/api/v1")

    assert client._url == "https://xi.fake.com/api/v1"
    assert str(client._client.base_url) == "https://xi.fake.com/api/v1/"
    assert client.experience._construct_url("foo") == "experiences/foo"
    assert client.relation._construct_url("foo") == "relations/foo"

    assert await client.close() is None
