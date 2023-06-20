"""Video plugin test fixtures."""

from dataclasses import dataclass
from datetime import datetime, timedelta

import pytest
from ralph.models.xapi.concepts.constants.video import RESULT_EXTENSION_TIME
from ralph.models.xapi.concepts.verbs.video import PlayedVerb
from warren.tests.fixtures.app import http_client  # noqa: F401
from warren.tests.fixtures.asynchronous import anyio_backend  # noqa: F401
from warren_video.factories import VideoPlayedFactory


@pytest.fixture
def non_mocked_hosts() -> list:
    """pytest-httpx: let requests to warren pass untouched."""
    return ["localhost"]


@pytest.fixture(scope="module")
def video_statements():
    """Generate test video statements."""

    @dataclass
    class VideoStatementParams:
        """Parameters for generating test video statements."""

        verb: str = PlayedVerb().id
        timestamp: datetime = datetime.utcnow()
        time: float = 0

    video_params = [
        VideoStatementParams(time=10),
        VideoStatementParams(time=20),
        VideoStatementParams(time=120),
        VideoStatementParams(timestamp=datetime.utcnow() - timedelta(weeks=10)),
    ]

    return [
        VideoPlayedFactory.build(
            [
                {
                    "object": {
                        "id": "uuid://ba4252ce-d042-43b0-92e8-f033f45612ee",
                        "objectType": "Activity",
                    }
                },
                {"verb": {"id": params.verb}},
                {"result": {"extensions": {RESULT_EXTENSION_TIME: params.time}}},
                {
                    "timestamp": params.timestamp.strftime("%Y-%m-%dT%H:%M:%S"),
                },
            ]
        )
        for params in video_params
    ]
