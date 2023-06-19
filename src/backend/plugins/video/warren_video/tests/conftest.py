"""Video plugin main fixtures."""

import pytest

from warren.conf import Settings

core_settings = Settings()


@pytest.fixture
def non_mocked_hosts() -> list:
    """pytest-httpx: let requests to warren pass untouched."""
    return ["localhost"]


FAKE_VIDEO_IDS = [
    "http://foo/bar",
    "http%3A%2F%2Ffoo%2Fbar",
    "uuid://foo/bar",
    "uuid%3A%2F%2Ffoo%2Fbar",
]
