"""Tests for Moodle indexers."""

import re
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from httpx import AsyncClient, HTTPError
from pydantic import ValidationError
from pytest_httpx import HTTPXMock
from sqlmodel import Session

from warren.conf import settings
from warren.xi.client import ExperienceIndex
from warren.xi.enums import AggregationLevel, Structure
from warren.xi.factories import ExperienceFactory
from warren.xi.indexers.moodle.client import Moodle
from warren.xi.indexers.moodle.etl import CourseContent, Courses
from warren.xi.indexers.moodle.models import Course, Module, Section
from warren.xi.models import ExperienceCreate, ExperienceRead


@pytest.mark.anyio
async def test_courses_factory(http_client: AsyncClient):
    """Test 'Courses' factory class method."""
    courses_instance = await Courses.factory(
        source=Moodle(),
        target=ExperienceIndex(),
    )

    assert isinstance(courses_instance, Courses)


@pytest.mark.anyio
async def test_course_content_factory(
    httpx_mock: HTTPXMock, db_session: Session, monkeypatch
):
    """Test 'CourseContent' factory class method in multiple scenario."""
    # Mock the experience index as localhost cannot be mocked due
    # to the non_mock_hosts fixture defined in the video plugin
    monkeypatch.setattr(settings, "SERVER_HOST", "mocked-xi")

    # Simulate experience not found by mocking the XI response
    wrong_iri = f"uuid://{uuid4().hex}"
    httpx_mock.add_response(
        url=re.compile(r".*experiences.*"),
        status_code=404,
    )

    # Attempt to build a 'CourseContent' indexer with a wrong iri
    with pytest.raises(ValueError, match=f"Wrong course IRI {wrong_iri}"):
        await CourseContent.factory(
            source=Moodle(),
            target=ExperienceIndex(),
            course_iri=wrong_iri,
        )

    # Generate random experience's data
    experience = ExperienceFactory.build_dict(exclude={}, json_dump={})

    experience["created_at"] = str(experience["created_at"])
    experience["updated_at"] = str(experience["updated_at"])

    # Return the generated experience by mocking the XI response
    httpx_mock.add_response(
        url=re.compile(r".*experiences.*"),
        json=experience,
    )

    # Attempt to get a 'CourseContent' indexer with a valid iri
    instance = await CourseContent.factory(
        source=Moodle(),
        target=ExperienceIndex(),
        course_iri=experience["iri"],
    )

    # Assert the factory method returned an indexer instance
    assert isinstance(instance, CourseContent)


@pytest.mark.anyio
async def test_course_content_course_id(http_client: AsyncClient):
    """Test '_course_id' property from 'CourseContent' with multiple scenario."""
    experience = ExperienceRead(
        **ExperienceFactory.build_dict(exclude={}, json_dump={})
    )

    # Build an IRI that doesn't contain any ID
    experience.iri = f"uuid://{uuid4().hex}"

    # Attempt parsing this valid IRI without ID
    indexer = CourseContent(lms=Moodle(), xi=ExperienceIndex(), course=experience)
    with pytest.raises(ValueError, match="Course ID not found in the course's IRI"):
        _ = indexer._course_id

    # Build an IRI that contains an ID
    experience.iri = "http://foo.com?id=1"

    # Attempt parsing this valid IRI with an ID
    indexer._course = experience
    assert indexer._course_id == 1

    # Build an IRI that contains multiple IDs
    experience.iri = "http://foo.com?id=3&id=4"

    # Assert that the first ID is retrieved
    indexer._course = experience
    assert indexer._course_id == 3


@pytest.mark.anyio
async def test_course_content_extract_error(http_client: AsyncClient):
    """Test '_extract' method from 'CourseContent' when encountering errors."""
    experience = ExperienceRead(
        **ExperienceFactory.build_dict(exclude={}, json_dump={})
    )

    # Build a valid IRI that doesn't contain an ID
    experience.iri = f"uuid://{uuid4().hex}"

    # Attempt extracting data when '_course_id' raises errors
    indexer = CourseContent(lms=Moodle(), xi=ExperienceIndex(), course=experience)
    with pytest.raises(ValueError, match="Course ID not found in the course's IRI"):
        await indexer._extract()


def test_courses_transform(http_client: AsyncClient):
    """Test '_transform' method from 'Courses' in multiple scenario."""
    lms_url = "http://foo.com"

    # Instantiate the 'Courses' indexer
    indexer = Courses(
        lms=Moodle(url=lms_url),
        xi=ExperienceIndex(),
    )

    # Attempt transforming an empty list of raw data
    assert [*indexer._transform(raw=[])] == []

    # Attempt transforming a list of raw data
    # todo - wrap in a polyfactory Factory
    raw = [
        Course(
            id=1,
            lang="fr",
            displayname="Lorem Ipsum",
            summary="",
            timecreated=1703147509,
            timemodified=1703153561,
        ),
        Course(
            id=2,
            lang="fr",
            displayname="Lorem Ipsum",
            summary="",
            timecreated=1703148709,
            timemodified=1703179561,
        ),
    ]
    assert [*indexer._transform(raw=raw)] == [
        ExperienceCreate(
            iri=f"{lms_url}/course/view.php?id={i+1}",
            title={"fr": "Lorem Ipsum"},
            language="fr",
            description={"fr": ""},
            structure=Structure.HIERARCHICAL,
            aggregation_level=AggregationLevel.THREE,
            technical_datatypes=[],
        )
        for i in range(2)
    ]


def test_course_content_transform(http_client: AsyncClient):
    """Test '_transform' method from 'CourseContent' in multiple scenario."""
    # Generate a random experience
    experience = ExperienceRead(
        **ExperienceFactory.build_dict(
            exclude={},
            json_dump={},
            iri="http://foo.com/course/view.php?id=1",
            language="fr",
        )
    )

    # Instantiate the 'CourseContent' indexer
    indexer = CourseContent(
        lms=Moodle(),
        xi=ExperienceIndex(),
        course=experience,
    )

    # Declare mocked raw data
    # todo - wrap in a polyfactory Factory
    raw = [
        Section(
            id=163,
            name="Lorem Ipsum",
            modules=[
                Module(
                    id=124,
                    url=None,
                    name="Lorem Ipsum",
                    modname="forum",
                    description="",
                ),
                Module(
                    id=125,
                    url="https://moodle.preprod-fun.apps.openfun.fr:443/mod/workshop/view.php?id=125",
                    name="Lorem Ipsum",
                    modname="workshop",
                    description=None,
                ),
            ],
        ),
        Section(
            id=164,
            name="Lorem Ipsum",
            modules=[
                Module(
                    id=126,
                    url="https://moodle.preprod-fun.apps.openfun.fr:443/mod/workshop/view.php?id=126",
                    name="Lorem Ipsum",
                    modname="workshop",
                    description="Lorem Ipsum",
                ),
            ],
        ),
    ]

    # Attempt transforming a list of raw data while ignoring validation errors
    assert [*indexer._transform(raw=raw)] == [
        ExperienceCreate(
            iri="https://moodle.preprod-fun.apps.openfun.fr:443/mod/workshop/view.php?id=125",
            title={"fr": "Lorem Ipsum"},
            language="fr",
            description={},
            structure=Structure.ATOMIC,
            aggregation_level=AggregationLevel.ONE,
            technical_datatypes=["workshop"],
        ),
        ExperienceCreate(
            iri="https://moodle.preprod-fun.apps.openfun.fr:443/mod/workshop/view.php?id=126",
            title={"fr": "Lorem Ipsum"},
            language="fr",
            description={"fr": "Lorem Ipsum"},
            structure=Structure.ATOMIC,
            aggregation_level=AggregationLevel.ONE,
            technical_datatypes=["workshop"],
        ),
    ]

    # Attempt transforming an empty list of raw data
    assert [*indexer._transform(raw=[])] == []

    # Attempt transforming a list of raw data while raising validation errors
    # Execution should stop when raising the first exception
    indexer._ignore_errors = False
    with pytest.raises(ValidationError):
        [*indexer._transform(raw=raw)]


@pytest.mark.anyio
async def test_courses_load_errors(
    httpx_mock: HTTPXMock, http_client: AsyncClient, monkeypatch
):
    """Test '_load' method from 'Courses' when encountering errors."""
    # Mock the experience index as localhost cannot be mocked due
    # to the non_mock_hosts fixture defined in the video plugin
    monkeypatch.setattr(settings, "SERVER_HOST", "mocked-xi")

    # Instantiate the 'Courses' indexer
    indexer = Courses(
        lms=Moodle(),
        xi=ExperienceIndex(),
    )

    # Mock data to be loaded
    data = [ExperienceCreate(**ExperienceFactory.build_dict())]

    # Mock any request made to create or update an experience
    httpx_mock.add_response(url=re.compile(r".*experiences.*"), status_code=404)

    # Attempt loading data with errors ignored
    # Execution should proceed
    await indexer._load(data=data)

    # Attempt loading data with errors raised
    # Execution should stop
    indexer._ignore_errors = False
    with pytest.raises(HTTPError):
        await indexer._load(data=data)

    # Attempt loading an empty list of data
    # It should not raise any error
    await indexer._load(data=[])


@pytest.mark.anyio
async def test_course_content_load_errors(
    httpx_mock: HTTPXMock, http_client: AsyncClient, monkeypatch
):
    """Test '_load' method from 'CourseContent' when encountering errors."""
    # Mock the experience index as localhost cannot be mocked due
    # to the non_mock_hosts fixture defined in the video plugin
    monkeypatch.setattr(settings, "SERVER_HOST", "mocked-xi")

    # Generate a random experience
    experience = ExperienceRead(
        **ExperienceFactory.build_dict(
            exclude={},
            json_dump={},
            iri="http://foo.com/course/view.php?id=1",
            language="fr",
        )
    )

    # Instantiate the 'CourseContent' indexer
    indexer = CourseContent(
        lms=Moodle(),
        xi=ExperienceIndex(),
        course=experience,
    )

    # Mock data to be loaded
    data = [ExperienceCreate(**ExperienceFactory.build_dict())]

    # Mock any request made to create or update an experience
    httpx_mock.add_response(url=re.compile(r".*experiences.*"), status_code=404)

    # Attempt loading data with errors ignored
    # Execution should proceed
    await indexer._load(data=data)

    # Attempt loading data with errors raised
    # Execution should stop
    indexer._ignore_errors = False
    with pytest.raises(HTTPError):
        await indexer._load(data=data)

    # Attempt loading an empty list of data
    # It should not raise any error
    await indexer._load(data=[])


@pytest.mark.anyio
async def test_course_content_load_create(
    httpx_mock: HTTPXMock, http_client: AsyncClient, monkeypatch
):
    """Test '_load' method from 'CourseContent' when creating new experience."""
    # Generate a random experience
    experience = ExperienceRead(
        **ExperienceFactory.build_dict(
            exclude={},
            json_dump={},
            iri="http://foo.com/course/view.php?id=1",
            language="fr",
        )
    )

    # Instantiate an indexer
    indexer = CourseContent(
        lms=Moodle(),
        xi=ExperienceIndex(),
        course=experience,
    )

    # Mock data to be loaded
    data = [ExperienceCreate(**ExperienceFactory.build_dict())]

    # Mock relation 'create_bidirectional' operation
    indexer._xi.relation.create_bidirectional = AsyncMock()

    # Mock experience 'create_or_update' operation to fake creation
    mocked_uuid = uuid4()
    indexer._xi.experience.create_or_update = AsyncMock(return_value=mocked_uuid)

    # Load data with mocked CRUD operations
    await indexer._load(data=data)

    # Assert 'create_bidirectional' has been called
    # It should be called only when creating new experiences
    indexer._xi.relation.create_bidirectional.assert_awaited_once()


@pytest.mark.anyio
async def test_course_content_load_update(
    httpx_mock: HTTPXMock, http_client: AsyncClient, monkeypatch
):
    """Test '_load' method from 'CourseContent' when updating experience."""
    # Generate a random experience
    experience = ExperienceRead(
        **ExperienceFactory.build_dict(
            exclude={},
            json_dump={},
            iri="http://foo.com/course/view.php?id=1",
            language="fr",
        )
    )

    # Instantiate an indexer
    indexer = CourseContent(
        lms=Moodle(),
        xi=ExperienceIndex(),
        course=experience,
    )

    # Mock data to be loaded
    data = [ExperienceCreate(**ExperienceFactory.build_dict())]

    # Mock relation 'create_bidirectional' operation
    indexer._xi.relation.create_bidirectional = AsyncMock()

    # Mock experience 'create_or_update' operation to fake update
    mocked_experience = ExperienceFactory.build()
    indexer._xi.experience.create_or_update = AsyncMock(return_value=mocked_experience)

    # Load data with mocked CRUD operations
    await indexer._load(data=data)

    # Assert 'create_bidirectional' has not been called
    # It should be called only when creating new experiences
    indexer._xi.relation.create_bidirectional.assert_not_awaited()
