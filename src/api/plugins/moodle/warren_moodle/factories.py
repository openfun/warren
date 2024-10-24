"""Factories for video xAPI events."""

from warren.factories.base import BaseXapiStatementFactory


# ruff: noqa: E501
class URLViewedFactory(BaseXapiStatementFactory):
    """URL viewed xAPI statement factory."""

    template: dict = {
        "actor": {
            "account": {
                "homePage": "http://lms.example.org",
                "name": "d5b3733b-ccd9-4ab1-bb29-22e3c2f2e592",
            },
            "name": "John Doe",
        },
        "object": {
            "id": "http://lms.example.org/mod/url/view.php?id=4",
            "definition": {
                "type": "http://adlnet.gov/expapi/activities/link",
                "name": {"en": "What is xAPI?"},
                "extensions": {
                    "https://w3id.org/learning-analytics/learning-management-system/external-id": ""
                },
            },
        },
        "verb": {
            "id": "http://id.tincanapi.com/verb/viewed",
            "display": {"en": "viewed"},
        },
        "timestamp": "2024-01-01T10:00:00+00:00",
        "context": {
            "platform": "Moodle",
            "language": "en",
            "extensions": {
                "http://lrs.learninglocker.net/define/extensions/info": {
                    "http://moodle.org": "4.1.10 (Build: 20240422)",
                    "https://github.com/xAPI-vle/moodle-logstore_xapi": "",
                    "event_name": "\\mod_url\\event\\course_module_viewed",
                    "event_function": "\\src\\transformer\\events\\mod_url\\course_module_viewed",
                }
            },
            "contextActivities": {
                "grouping": [
                    {
                        "id": "http://lms.example.org",
                        "definition": {
                            "type": "http://id.tincanapi.com/activitytype/lms",
                            "name": {"en": "LMS Example"},
                        },
                    },
                    {
                        "id": "http://lms.example.org/course/view.php?id=8",
                        "definition": {
                            "type": "http://id.tincanapi.com/activitytype/lms/course",
                            "name": {"en": "xAPI 101"},
                            "extensions": {
                                "https://w3id.org/learning-analytics/learning-management-system/short-id": "",
                                "https://w3id.org/learning-analytics/learning-management-system/external-id": "",
                            },
                        },
                    },
                ],
                "category": [
                    {
                        "id": "http://moodle.org",
                        "definition": {
                            "type": "http://id.tincanapi.com/activitytype/source",
                            "name": {"en": "Moodle"},
                        },
                    }
                ],
            },
        },
        "id": "fc97bf06-4059-45a5-a862-9da47f0b3741",
        "stored": "2024-01-01T11:00:00.000000+00:00",
        "authority": {"mbox": "mailto:admin@lms-example.com", "objectType": "Agent"},
    }
