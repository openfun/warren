"""Lrs test fixtures."""
from dataclasses import dataclass
from datetime import datetime
from typing import List
from urllib.parse import ParseResult, quote_plus, unquote, urlencode, urlparse

from ralph.models.xapi.base.verbs import BaseXapiVerb
from ralph.models.xapi.concepts.constants.video import RESULT_EXTENSION_TIME
from ralph.models.xapi.concepts.verbs.scorm_profile import CompletedVerb
from ralph.models.xapi.concepts.verbs.video import PlayedVerb
from ralph.models.xapi.video.statements import BaseVideoStatement
from warren.backends import lrs_client
from warren.conf import Settings
from warren.filters import DatetimeRange
from warren_video.tests.factories import VideoCompletedFactory, VideoPlayedFactory

core_settings = Settings()


def create_lrs_url(
    base_url: str,
    video_id: str,
    verb: BaseXapiVerb,
    date_range: DatetimeRange,
) -> str:
    """Mock a video played LRS request."""
    date_params = {
        "since": date_range.since.astimezone().isoformat(),
        "until": date_range.until.astimezone().isoformat(),
    }

    query_string = (
        f"verb={quote_plus(verb.id, safe='/')}&activity="
        f"{quote_plus(unquote(video_id), safe='/')}"
    )

    return ParseResult(
        scheme=urlparse(base_url).scheme,
        netloc=urlparse(base_url).netloc,
        path="/xAPI/statements",
        query=f"{query_string}&{urlencode({**date_params, 'limit': 500})}",
        params="",
        fragment="",
    ).geturl()


def mock_video_lrs_request(
    httpx_mock,
    video_id: str,
    verb: BaseXapiVerb,
    date_range: DatetimeRange,
    statements: List,
):
    """Mock a video played LRS request."""
    base_url = "http://fake-lrs.com"
    lrs_client.base_url = base_url

    date_params = {
        "since": date_range.since.astimezone().isoformat(),
        "until": date_range.until.astimezone().isoformat(),
    }

    query_string = (
        f"verb={quote_plus(verb.id, safe='/')}&activity="
        f"{quote_plus(unquote(video_id), safe='/')}"
    )

    lrs_url = ParseResult(
        scheme=urlparse(lrs_client.base_url).scheme,
        netloc=urlparse(lrs_client.base_url).netloc,
        path=lrs_client.statements_endpoint,
        query=f"{query_string}&{urlencode({**date_params, 'limit': 500})}",
        params="",
        fragment="",
    ).geturl()

    httpx_mock.add_response(
        url=lrs_url, method="GET", json={"statements": statements}, status_code=200
    )


@dataclass
class VideoStatementParams:
    """Parameters for generating test video statements."""

    timestamp: datetime = datetime.utcnow()
    time: float = 0


def make_video_statements(
    video_params: List[VideoStatementParams], verb: BaseXapiVerb
) -> List[BaseVideoStatement]:
    """Generate a list of video statements."""
    if verb == PlayedVerb():
        factory = VideoPlayedFactory
    elif verb == CompletedVerb():
        factory = VideoCompletedFactory
    else:
        raise ValueError(f"Unknown verb {verb}")

    return [
        factory.build(
            [
                {"result": {"extensions": {RESULT_EXTENSION_TIME: video_param.time}}},
                {
                    "timestamp": video_param.timestamp.strftime("%Y-%m-%dT%H:%M:%S"),
                },
            ]
        )
        for video_param in video_params
    ]
