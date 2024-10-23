"""Factories for document xAPI events."""

from ralph.models.xapi.lms.statements import LMSDownloadedDocument
from warren.factories.base import BaseXapiStatementFactory


class LMSDownloadedDocumentFactory(BaseXapiStatementFactory):
    """LMSDownloadedDocument xAPI statement factory."""

    template: dict = {
        "verb": {
            "id": "http://id.tincanapi.com/verb/downloaded",
            "display": {"en-US": "downloaded"},
        },
        "context": {
            "extensions": {
                "https://w3id.org/xapi/cmi5/context/extensions/sessionid": "53ff781a-3c52-11ee-be56-0242ac120002"  # noqa: E501
            },
            "contextActivities": {
                "category": [
                    {
                        "id": "https://w3id.org/xapi/lms",
                        "definition": {
                            "type": "http://adlnet.gov/expapi/activities/profile"
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
                "type": "http://id.tincanapi.com/activitytype/document",
                "name": {"en-US": "xAPI 101 Introduction notes"},
            },
            "id": "uuid://dd38149d-956a-483d-8975-c1506de1e1a9",
        },
        "timestamp": "2021-12-01T08:17:47.150905+00:00",
    }
    model: LMSDownloadedDocument = LMSDownloadedDocument
