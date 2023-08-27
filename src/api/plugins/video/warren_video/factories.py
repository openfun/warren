"""Factories for video xAPI events."""
from ralph.models.xapi.concepts.constants.video import RESULT_EXTENSION_TIME
from ralph.models.xapi.video.statements import (
    VideoDownloaded,
    VideoInitialized,
    VideoPlayed,
)
from warren.factories.base import BaseXapiStatementFactory


class VideoPlayedFactory(BaseXapiStatementFactory):
    """VideoPlayed xAPI statement factory."""

    template: dict = {
        "verb": {
            "id": "https://w3id.org/xapi/video/verbs/played",
            "display": {"en-US": "played"},
        },
        "context": {
            "extensions": {
                "https://w3id.org/xapi/video/extensions/session-id": (
                    "1be53154-aed0-5aab-9485-b773e7efaf24"
                )
            },
            "contextActivities": {
                "category": [
                    {
                        "id": "https://w3id.org/xapi/video",
                        "definition": {
                            "id": "uuid://C678149d-956a-483d-8975-c1506de1e1a9",
                            "definition": {
                                "type": "http://adlnet.gov/expapi/activities/profile"
                            },
                        },
                    }
                ],
                "parent": [
                    {
                        "id": "course-v1:FUN-MOOC+00001+session01",
                        "objectType": "Activity",
                        "definition": {
                            "type": "http://adlnet.gov/expapi/activities/course"
                        },
                    }
                ],
            },
        },
        "result": {"extensions": {RESULT_EXTENSION_TIME: 10.0}},
        "id": "2140967b-563b-464b-90c0-2e114bd8e133",
        "actor": {
            "objectType": "Agent",
            "account": {
                "name": "d5b3733b-ccd9-4ab1-bb29-22e3c2f2e592",
                "homePage": "http://lms.example.org",
            },
        },
        "object": {
            "definition": {
                "type": "https://w3id.org/xapi/video/activity-type/video",
                "name": {"en-US": "Learning analytics 101"},
            },
            "id": "uuid://dd38149d-956a-483d-8975-c1506de1e1a9",
            "objectType": "Activity",
        },
        "timestamp": "2021-12-01T08:17:47.150905+00:00",
    }
    model: VideoPlayed = VideoPlayed


class VideoDownloadedFactory(BaseXapiStatementFactory):
    """VideoDownloaded xAPI statement factory."""

    template: dict = {
        "verb": {
            "id": "http://id.tincanapi.com/verb/downloaded",
            "display": {"en-US": "downloaded"},
        },
        "context": {
            "extensions": {
                "https://w3id.org/xapi/video/extensions/session-id": (
                    "6e952c73-71e3-5c8c-837b-39baea0e73b9"
                ),
                "https://w3id.org/xapi/video/extensions/quality": 720,
                "https://w3id.org/xapi/video/extensions/length": 508,
            },
            "contextActivities": {
                "category": [
                    {
                        "id": "https://w3id.org/xapi/video",
                        "definition": {
                            "id": "uuid://C678149d-956a-483d-8975-c1506de1e1a9",
                            "definition": {
                                "type": "http://adlnet.gov/expapi/activities/profile"
                            },
                        },
                    }
                ],
                "parent": [
                    {
                        "id": "course-v1:FUN-MOOC+00001+session01",
                        "objectType": "Activity",
                        "definition": {
                            "type": "http://adlnet.gov/expapi/activities/course"
                        },
                    }
                ],
            },
        },
        "id": "2140967b-563b-464b-90c0-2e114bd8e133",
        "actor": {
            "objectType": "Agent",
            "account": {
                "name": "d5b3733b-ccd9-4ab1-bb29-22e3c2f2e592",
                "homePage": "http://lms.example.org",
            },
        },
        "object": {
            "definition": {
                "type": "https://w3id.org/xapi/video/activity-type/video",
                "name": {"en-US": "Learning analytics 101"},
            },
            "id": "uuid://dd38149d-956a-483d-8975-c1506de1e1a9",
            "objectType": "Activity",
        },
        "timestamp": "2021-12-01T08:17:47.150905+00:00",
    }
    model: VideoPlayed = VideoDownloaded


class VideoInitializedFactory(BaseXapiStatementFactory):
    """VideoInitialized xAPI statement factory."""

    template: dict = {
        "verb": {
            "id": "http://adlnet.gov/expapi/verbs/initialized",
            "display": {"en-US": "initialized"},
        },
        "context": {
            "extensions": {
                "https://w3id.org/xapi/video/extensions/session-id": (
                    "1be53154-aed0-5aab-9485-b773e7efaf24"
                ),
                "https://w3id.org/xapi/video/extensions/length": 480,
                "https://w3id.org/xapi/video/extensions/completion-threshold": 0.9,
            },
            "contextActivities": {
                "category": [
                    {
                        "id": "https://w3id.org/xapi/video",
                        "definition": {
                            "id": "uuid://C678149d-956a-483d-8975-c1506de1e1a9",
                            "definition": {
                                "type": "http://adlnet.gov/expapi/activities/profile"
                            },
                        },
                    }
                ],
                "parent": [
                    {
                        "id": "course-v1:FUN-MOOC+00001+session01",
                        "objectType": "Activity",
                        "definition": {
                            "type": "http://adlnet.gov/expapi/activities/course"
                        },
                    }
                ],
            },
        },
        "id": "2140967b-563b-464b-90c0-2e114bd8e133",
        "actor": {
            "objectType": "Agent",
            "account": {
                "name": "d5b3733b-ccd9-4ab1-bb29-22e3c2f2e592",
                "homePage": "http://lms.example.org",
            },
        },
        "object": {
            "definition": {
                "type": "https://w3id.org/xapi/video/activity-type/video",
                "name": {"en-US": "Learning analytics 101"},
            },
            "id": "uuid://dd38149d-956a-483d-8975-c1506de1e1a9",
            "objectType": "Activity",
        },
        "timestamp": "2021-12-01T08:17:47.150905+00:00",
    }
    model: VideoInitialized = VideoInitialized
