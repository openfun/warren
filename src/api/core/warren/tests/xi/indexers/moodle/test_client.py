"""Tests for Moodle client."""

import re

import pytest
from httpx import HTTPError, ReadTimeout
from pydantic import ValidationError
from pytest_httpx import HTTPXMock

from warren.xi.indexers.exceptions import IndexerQueryException
from warren.xi.indexers.moodle.client import Moodle
from warren.xi.indexers.moodle.models import Course, Module, Section


@pytest.mark.anyio
async def test_get(httpx_mock: HTTPXMock):
    """Test '_get' method from 'Moodle' client in multiple scenario."""
    client = Moodle()

    # Assert '_get' raises exception when encountering HTTP errors
    httpx_mock.add_response(
        method="POST", url=re.compile(r".*webservice.*"), status_code=404
    )
    with pytest.raises(HTTPError):
        await client._get(wsfunction="foo.")

    # Assert '_get' raises exception when encountering a ReadTimeout error
    httpx_mock.add_exception(ReadTimeout("Unable to read within timeout"))
    with pytest.raises(
        IndexerQueryException,
        match="Timed out while receiving data from the host. Try increasing the "
        "request timeout.",
    ):
        await client._get(wsfunction="foo.")

    # Assert '_get' raises exception when encountering Moodle exception
    httpx_mock.add_response(
        method="POST",
        url=re.compile(r".*webservice.*"),
        status_code=200,
        json={
            "exception": "moodle_exception",
            "errorcode": "invalidtoken",
            "message": "Jeton invalide (introuvable)",
        },
    )
    with pytest.raises(
        IndexerQueryException, match="An error occurred while querying Moodle API"
    ):
        await client._get(wsfunction="foo.")

    # Assert '_get' returns a dict response
    httpx_mock.add_response(
        method="POST", url=re.compile(r".*webservice.*"), json=[{"foo": "John Doe"}]
    )
    assert await client._get(wsfunction="foo.") == [{"foo": "John Doe"}]


@pytest.mark.anyio
async def test_get_courses(httpx_mock: HTTPXMock):
    """Test 'get_courses' method from 'Moodle' client in multiple scenario."""
    client = Moodle()

    # Fetch an empty list of courses
    httpx_mock.add_response(
        method="POST",
        url=re.compile(r".*webservice.*"),
        json=[],
    )
    assert await client.get_courses() == []

    # Fetch a list of wrongly formatted courses
    httpx_mock.add_response(
        method="POST",
        url=re.compile(r".*webservice.*"),
        json=[
            {
                "foo.": "John Doe",
            },
            {
                "foo.": "Martin Thomas",
            },
        ],
    )
    with pytest.raises(ValidationError):
        await client.get_courses()

    # Fetch a valid course
    # todo - extract this in the factory
    httpx_mock.add_response(
        method="POST",
        url=re.compile(r".*webservice.*"),
        json=[
            {
                "id": 30,
                "shortname": "Lorem",
                "categoryid": 12,
                "categorysortorder": 0,
                "fullname": "Lorem ipsum dolor sit amet",
                "displayname": "Lorem Ipsum",
                "idnumber": "",
                "summary": "",
                "summaryformat": 1,
                "format": "topics",
                "showgrades": 1,
                "newsitems": 5,
                "startdate": 1703203200,
                "enddate": 1734739200,
                "numsections": 5,
                "maxbytes": 0,
                "showreports": 0,
                "visible": 1,
                "hiddensections": 1,
                "groupmode": 1,
                "groupmodeforce": 0,
                "defaultgroupingid": 0,
                "timecreated": 1703147509,
                "timemodified": 1703153561,
                "enablecompletion": 1,
                "completionnotify": 0,
                "lang": "fr",
                "forcetheme": "",
            }
        ],
    )
    assert await client.get_courses() == [
        Course(
            id=30,
            lang="fr",
            displayname="Lorem Ipsum",
            summary="",
            timecreated=1703147509,
            timemodified=1703153561,
        )
    ]


@pytest.mark.anyio
async def test_get_course_contents(httpx_mock: HTTPXMock):
    """Test 'get_course_contents' method from 'Moodle' client in multiple scenario."""
    client = Moodle()

    # Fetch an empty list of sections
    httpx_mock.add_response(
        method="POST",
        url=re.compile(r".*webservice.*"),
        json=[],
    )
    assert await client.get_course_contents(course_id=1) == []

    # Fetch a list of wrongly formatted sections
    httpx_mock.add_response(
        method="POST",
        url=re.compile(r".*webservice.*"),
        json=[
            {
                "foo.": "John Doe",
            },
            {
                "foo.": "Martin Thomas",
            },
        ],
    )
    with pytest.raises(ValidationError):
        await client.get_course_contents(course_id=1)

    # Fetch a valid section
    # todo - extract this in the factory
    httpx_mock.add_response(
        method="POST",
        url=re.compile(r".*webservice.*"),
        json=[
            {
                "id": 163,
                "name": "Lorem Ipsum",
                "visible": 1,
                "summary": "",
                "summaryformat": 1,
                "section": 0,
                "hiddenbynumsections": 0,
                "uservisible": True,
                "modules": [
                    {
                        "id": 194,
                        "url": None,
                        "name": "Annonces",
                        "instance": 47,
                        "contextid": 325,
                        "visible": 1,
                        "uservisible": True,
                        "visibleoncoursepage": 1,
                        "modicon": "https://moodle.preprod-fun.apps.openfun.fr:443/theme/image.php/boost/forum/1703697967/monologo?filtericon=1",
                        "modname": "forum",
                        "modplural": "Forums",
                        "availability": None,
                        "indent": 0,
                        "onclick": "",
                        "afterlink": None,
                        "customdata": '""',
                        "noviewlink": False,
                        "completion": 0,
                        "downloadcontent": 1,
                        "dates": [],
                    },
                    {
                        "id": 195,
                        "url": "https://moodle.preprod-fun.apps.openfun.fr:443/mod/workshop/view.php?id=127",
                        "name": "Activité Atelier",
                        "instance": 3,
                        "contextid": 226,
                        "description": "",
                        "visible": 1,
                        "uservisible": True,
                        "visibleoncoursepage": 1,
                        "modicon": "https://moodle.preprod-fun.apps.openfun.fr:443/theme/image.php/boost/workshop/1703698702/monologo?filtericon=1",
                        "modname": "workshop",
                        "modplural": "Ateliers",
                        "availability": None,
                        "indent": 0,
                        "onclick": "",
                        "afterlink": None,
                        "customdata": '""',
                        "noviewlink": False,
                        "completion": 1,
                        "completiondata": {
                            "state": 0,
                            "timecompleted": 0,
                            "overrideby": None,
                            "valueused": False,
                            "hascompletion": True,
                            "isautomatic": False,
                            "istrackeduser": True,
                            "uservisible": True,
                            "details": [],
                        },
                        "downloadcontent": 1,
                        "dates": [],
                    },
                ],
            }
        ],
    )
    assert await client.get_course_contents(course_id=1) == [
        Section(
            id=163,
            name="Lorem Ipsum",
            modules=[
                Module(
                    id=194,
                    url=None,
                    name="Annonces",
                    modname="forum",
                    description=None,
                ),
                Module(
                    id=195,
                    url="https://moodle.preprod-fun.apps.openfun.fr:443/mod/workshop/view.php?id=127",
                    name="Activité Atelier",
                    modname="workshop",
                    description="",
                ),
            ],
        )
    ]
