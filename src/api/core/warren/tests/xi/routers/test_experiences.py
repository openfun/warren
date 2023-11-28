"""Tests for the experience index API '/experience' endpoints."""

# ruff: noqa: S311

from datetime import timezone
from typing import Any
from uuid import uuid4

import pytest
from freezegun import freeze_time
from httpx import AsyncClient
from sqlmodel import Session, select

from warren.xi.factories import (
    ExperienceFactory,
    RelationFactory,
)
from warren.xi.models import (
    AggregationLevel,
    Experience,
    Structure,
)


@pytest.mark.anyio
async def test_experience_create(http_client: AsyncClient, db_session: Session):
    """Test creating an experience with valid data."""
    ExperienceFactory.__session__ = db_session

    # Assert the database is empty
    experiences = db_session.exec(select(Experience)).all()
    assert len(experiences) == 0

    # Generate randomized valid experience data
    experience_data = ExperienceFactory.build_dict()

    # Attempt creating a first experience with valid data
    time = ExperienceFactory.__faker__.date_time(timezone.utc).isoformat()
    with freeze_time(time):
        response = await http_client.post("/api/v1/experiences/", json=experience_data)
        response_data = response.json()

    assert response.status_code == 200

    # Verify that the first experience has been correctly saved
    assert db_session.get(Experience, response_data) == Experience(
        id=response_data,
        created_at=time,
        updated_at=time,
        relations_source=[],
        relations_target=[],
        **experience_data,
    )

    # Assert the database contains one experience
    experiences = db_session.exec(select(Experience)).all()
    assert len(experiences) == 1


@pytest.mark.anyio
async def test_experience_create_multiple(
    http_client: AsyncClient, db_session: Session
):
    """Test creating multiple experiences with valid data."""
    ExperienceFactory.__session__ = db_session

    # Assert the database is empty
    experiences = db_session.exec(select(Experience)).all()
    assert len(experiences) == 0

    for n in range(1, 10):
        # Generate randomized valid experience data
        experience_data = ExperienceFactory.build_dict()

        # Attempt creating a first experience with valid data
        time = ExperienceFactory.__faker__.date_time(timezone.utc).isoformat()
        with freeze_time(time):
            response = await http_client.post(
                "/api/v1/experiences/", json=experience_data
            )
            response_data = response.json()

        assert response.status_code == 200

        # Verify that the first experience has been correctly saved
        assert db_session.get(Experience, response_data) == Experience(
            id=response_data,
            created_at=time,
            updated_at=time,
            relations_source=[],
            relations_target=[],
            **experience_data,
        )

        # Assert the database contains one experience
        experiences = db_session.exec(select(Experience)).all()
        assert len(experiences) == n


@pytest.mark.anyio
async def test_experience_create_empty(http_client: AsyncClient, db_session: Session):
    """Test creating an empty experience."""
    # Attempt to create an empty experience
    response = await http_client.post("/api/v1/experiences/", json={})

    # Experience's creation should fail
    assert response.status_code == 422


@pytest.mark.anyio
async def test_experience_create_without_duration(
    http_client: AsyncClient, db_session: Session
):
    """Test creating experiences without the optional duration."""
    # Generate randomized valid experience data
    experience_data = ExperienceFactory.build_dict(duration=None)

    # Attempt to create an experience without duration
    time = ExperienceFactory.__faker__.date_time(timezone.utc).isoformat()
    with freeze_time(time):
        response = await http_client.post("/api/v1/experiences/", json=experience_data)
        response_data = response.json()

    assert response.status_code == 200

    # Verify that the experience has been correctly saved
    assert db_session.get(Experience, response_data) == Experience(
        id=response_data,
        created_at=time,
        updated_at=time,
        relations_source=[],
        relations_target=[],
        **experience_data,
    )

    # Assert the database contains one experience
    experiences = db_session.exec(select(Experience)).all()
    assert len(experiences) == 1


@pytest.mark.anyio
async def test_experience_create_duplicated_iri(
    http_client: AsyncClient, db_session: Session
):
    """Test creating an experience with a duplicated IRI."""
    ExperienceFactory.__session__ = db_session
    duplicated_iri = f"uuid://{uuid4().hex}"

    # Create an experience in the database with a specific IRI
    ExperienceFactory.create_sync(iri=duplicated_iri)

    # Assert the database contains one experience
    experiences = db_session.exec(select(Experience)).all()
    assert len(experiences) == 1

    # Attempt creating another experience with the same IRI
    response = await http_client.post(
        "/api/v1/experiences/", json=ExperienceFactory.build_dict(iri=duplicated_iri)
    )

    # Experience's creation should fail due to IRI uniqueness
    assert response.status_code == 500
    assert response.json() == {
        "detail": "An error occurred while creating the experience"
    }


@pytest.mark.anyio
@pytest.mark.parametrize(
    "invalid_data",
    [
        {"iri": "wrong-uuid"},
        {"duration": "foo."},
        {"title": 123},
        {"title": {"en": "Lesson 1"}},  # not a string
        {"aggregation_level": 5},  # outside range
        {"aggregation_level": 0},  # outside range
        {"structure": "random structure"},
        {"structure": "Atomic"},  # wrongly capitalize
        {"language": "a" * 200},  # too long
        {"duration": -100},  # negative duration
        {"duration": 0},  # null duration
    ],
)
async def test_experience_create_invalid(
    http_client: AsyncClient, db_session: Session, invalid_data: dict
):
    """Test creating an experience with invalid data."""
    # Invalid data for creating an experience
    invalid_data = ExperienceFactory.build_dict().update(invalid_data)

    # Attempt creating an experience with invalid data
    response = await http_client.post(
        "/api/v1/experiences/",
        json=invalid_data,
    )
    assert response.status_code == 422

    # Assert the database is empty
    experiences = db_session.exec(select(Experience)).all()
    assert len(experiences) == 0


@pytest.mark.anyio
@pytest.mark.parametrize(
    "number_experiences",
    [100, 0],
)
async def test_experience_read(
    http_client: AsyncClient, db_session: Session, number_experiences: int
):
    """Test retrieving detailed information about an experience."""
    ExperienceFactory.__session__ = db_session

    # Create some experiences in the database
    if number_experiences:
        ExperienceFactory.create_batch_sync(number_experiences)

    # Create an experience
    creation_date = ExperienceFactory.__faker__.date_time(timezone.utc)
    with freeze_time(creation_date):
        experience = ExperienceFactory.create_sync()

    # Attempt to read the last created experience
    response = await http_client.get(f"/api/v1/experiences/{experience.id}")
    assert response.status_code == 200

    # Verify the retrieved data matches the expected format
    assert response.json() == {
        **experience.dict(),
        "id": str(experience.id),
        "created_at": creation_date.isoformat(),
        "updated_at": creation_date.isoformat(),
        "relations_source": [],
        "relations_target": [],
    }

    # Assert the database still contains the right number of experiences
    experiences = db_session.exec(select(Experience)).all()
    assert len(experiences) == number_experiences + 1


@pytest.mark.anyio
@pytest.mark.parametrize("invalid_id", ["foo", 123, "a1-a2-aa", uuid4().hex + "a"])
async def test_experience_read_invalid(
    http_client: AsyncClient, db_session: Session, invalid_id: Any
):
    """Test retrieving an experience with an invalid or nonexistent ID."""
    ExperienceFactory.__session__ = db_session

    # Create some experiences in the database
    number_experiences = 10
    ExperienceFactory.create_batch_sync(number_experiences)

    # Attempt to read an experience with an invalid ID
    response = await http_client.get(f"/api/v1/experiences/{invalid_id}")
    assert response.status_code == 422

    # Attempt to read an experience with a nonexistent ID
    nonexistent_id = uuid4().hex
    response = await http_client.get(f"/api/v1/experiences/{nonexistent_id}")
    assert response.status_code == 404
    assert response.json() == {"detail": "Experience not found"}

    # Assert the database still contains the same number of experiences
    experiences = db_session.exec(select(Experience)).all()
    assert len(experiences) == number_experiences


@pytest.mark.anyio
async def test_experience_read_with_relation(http_client: AsyncClient, db_session):
    """Test retrieving experiences with a relation."""
    ExperienceFactory.__session__ = RelationFactory.__session__ = db_session

    # Create some experiences in the database
    number_experiences = 10
    ExperienceFactory.create_batch_sync(number_experiences)

    time = ExperienceFactory.__faker__.date_time(timezone.utc).isoformat()
    with freeze_time(time):
        relation = RelationFactory.create_sync()

    db_session.refresh(relation)

    # Attempt to read the source experience
    response = await http_client.get(f"/api/v1/experiences/{relation.source_id}")
    response_data = response.json()
    assert response.status_code == 200

    expected_relation = {
        "id": str(relation.id),
        "source_id": str(relation.source_id),
        "target_id": str(relation.target_id),
        "kind": relation.kind,
        "created_at": time,
        "updated_at": time,
    }
    # Verify the source data matches the expected format
    assert response_data["relations_source"] == [expected_relation]
    assert response_data["relations_target"] == []

    # Attempt to read the target experience
    response = await http_client.get(f"/api/v1/experiences/{relation.target_id}")
    response_data = response.json()
    assert response.status_code == 200

    # Verify the retrieved data matches the expected format
    assert response_data["relations_source"] == []
    assert response_data["relations_target"] == [expected_relation]

    # Assert the database contains the right number of experiences
    experiences = db_session.exec(select(Experience)).all()
    assert len(experiences) == number_experiences + 2


@pytest.mark.anyio
@pytest.mark.parametrize(
    "update_data",
    [
        {"iri": f"uuid://{uuid4().hex}"},
        {
            "title": {"en": ExperienceFactory.__faker__.sentence(nb_words=5)},
            "duration": ExperienceFactory.__faker__.pyint(),
        },
        {"description": {"en": ExperienceFactory.__faker__.paragraph(nb_sentences=1)}},
        {
            "structure": ExperienceFactory.__random__.choice(list(Structure)),
            "iri": f"uuid://{uuid4().hex}",
        },
        {
            "aggregation_level": ExperienceFactory.__random__.choice(
                list(AggregationLevel)
            ),
            "iri": f"uuid://{uuid4().hex}",
        },
    ],
)
async def test_experience_update(
    http_client: AsyncClient, db_session: Session, update_data: dict
):
    """Test updating an experience with various update scenarios."""
    ExperienceFactory.__session__ = db_session

    # Get two random dates for creating and updating an experience
    creation_date = ExperienceFactory.__faker__.date_time(timezone.utc)
    update_date = ExperienceFactory.__faker__.date_time_between(
        creation_date, tzinfo=timezone.utc
    )

    # Create an experience in the database
    with freeze_time(creation_date):
        experience = ExperienceFactory.create_sync()

    # Assert the initial 'updated_at' field is equal to the creation date
    assert experience.updated_at == creation_date

    # Update the experience with some valid data
    with freeze_time(update_date):
        response = await http_client.put(
            f"/api/v1/experiences/{experience.id}",
            json=update_data,
        )
        response_data = response.json()

    assert response.status_code == 200

    # Check if specified fields in the response match the expected values
    for key, value in update_data.items():
        assert response_data[key] == value

    # Check untouched fields in the response match the initial values
    for key, value in experience.dict(
        exclude={"created_at", "updated_at", *update_data.keys()}
    ):
        assert response_data[key] == value

    # Assert that the 'updated_at' field has been updated
    assert response_data["updated_at"] == update_date.isoformat()

    # Assert that the 'created_at' field has not been updated
    assert response_data["created_at"] == creation_date.isoformat()

    # Assert the update has not created any new experience
    experiences = db_session.exec(select(Experience)).all()
    assert len(experiences) == 1


@pytest.mark.anyio
async def test_experience_update_duplicated_IRI(
    http_client: AsyncClient, db_session: Session
):
    """Test updating an experience with an existing IRI."""
    ExperienceFactory.__session__ = db_session

    # Create two experiences in the database
    first_experience, second_experience = ExperienceFactory.create_batch_sync(2)

    # Attempt to update the second experience with first experience's IRI
    response = await http_client.put(
        f"/api/v1/experiences/{second_experience.id}",
        json={"iri": first_experience.iri},
    )

    # Assert the update fails because of IRI uniqueness
    assert response.status_code == 500
    assert response.json() == {
        "detail": "An error occurred while updating the experience"
    }


@pytest.mark.anyio
@pytest.mark.parametrize(
    "invalid_data",
    [
        {"iri": "wrong-uuid"},
        {"duration": "foo."},
        {"title": 123},
        {"technical_datatypes": "hello world."},
    ],
)
async def test_experience_update_invalid(
    http_client: AsyncClient, db_session: Session, invalid_data: dict
):
    """Test updating an experience with invalid data."""
    ExperienceFactory.__session__ = db_session

    # Create an experience in the database
    experience = ExperienceFactory.create_sync()

    # Attempt to update an experience with an invalid ID
    wrong_id = uuid4().hex
    response = await http_client.put(
        f"/api/v1/experiences/{wrong_id}", json={"iri": "uuid://foo."}
    )
    assert response.status_code == 404
    assert response.json() == {"detail": "Experience not found"}

    # Attempt to update an experience with invalid data
    response = await http_client.put(
        f"/api/v1/experiences/{experience.id}",
        json=invalid_data,
    )
    assert response.status_code == 422

    # Assert the update has not created any new experience
    experiences = db_session.exec(select(Experience)).all()
    assert len(experiences) == 1


@pytest.mark.anyio
async def test_experience_update_same(http_client: AsyncClient, db_session: Session):
    """Test updating an experience with the same data."""
    ExperienceFactory.__session__ = db_session

    # Get two random dates for creating and updating an experience
    creation_date = ExperienceFactory.__faker__.date_time(timezone.utc)
    update_date = ExperienceFactory.__faker__.date_time_between(
        creation_date, tzinfo=timezone.utc
    )

    # Create an experience in the database
    with freeze_time(creation_date):
        experience = ExperienceFactory.create_sync()

    # Get experience's data
    db_session.refresh(experience)
    experience_data = experience.dict(exclude={"id", "created_at", "updated_at"})

    # Update the experience with the same data
    with freeze_time(update_date):
        response = await http_client.put(
            f"/api/v1/experiences/{experience.id}",
            json=experience_data,
        )
        response_data = response.json()

    assert response.status_code == 200

    # 'updated_at' field should not be updated when there is no real update to the data
    assert response_data["updated_at"] == creation_date.isoformat()

    #  Assert data has not changed
    assert response_data == {
        **experience_data,
        "id": str(experience.id),
        "created_at": creation_date.isoformat(),
        "updated_at": creation_date.isoformat(),
        "relations_source": [],
        "relations_target": [],
    }

    # Assert the update has not created any new experience
    experiences = db_session.exec(select(Experience)).all()
    assert len(experiences) == 1


@pytest.mark.anyio
async def test_experience_update_empty(http_client: AsyncClient, db_session: Session):
    """Test updating an experience with empty data."""
    ExperienceFactory.__session__ = db_session

    # Get two random dates for creating and updating an experience
    creation_date = ExperienceFactory.__faker__.date_time(timezone.utc)
    update_date = ExperienceFactory.__faker__.date_time_between(
        creation_date, tzinfo=timezone.utc
    )

    # Create an experience in the database
    with freeze_time(creation_date):
        experience = ExperienceFactory.create_sync()

    # Get experience's data
    db_session.refresh(experience)
    experience_data = experience.dict(exclude={"id", "created_at", "updated_at"})

    # Update the experience with the same data
    with freeze_time(update_date):
        response = await http_client.put(
            f"/api/v1/experiences/{experience.id}",
            json={},
        )
        response_data = response.json()

    assert response.status_code == 200

    # 'updated_at' field should not be updated when there is no real update to the data
    assert response_data["updated_at"] == creation_date.isoformat()

    #  Assert data has not changed
    assert response_data == {
        **experience_data,
        "id": str(experience.id),
        "created_at": creation_date.isoformat(),
        "updated_at": creation_date.isoformat(),
        "relations_source": [],
        "relations_target": [],
    }

    # Assert the update has not created any new experience
    experiences = db_session.exec(select(Experience)).all()
    assert len(experiences) == 1


@pytest.mark.anyio
async def test_experiences_read_default(http_client: AsyncClient, db_session: Session):
    """Test the default behavior of retrieving experiences."""
    ExperienceFactory.__session__ = db_session

    # Attempt to retrieve experiences when the database is empty
    response = await http_client.get("/api/v1/experiences/")
    assert response.status_code == 200
    assert response.json() == []

    # Create some experiences in the database
    number_experiences = 200
    ExperienceFactory.create_batch_sync(number_experiences)

    experiences = db_session.exec(select(Experience)).all()

    # Retrieve experiences without any query parameters
    response = await http_client.get("/api/v1/experiences/")
    response_data = response.json()
    assert response.status_code == 200

    # Assert that the number of experiences matches the default limit (100)
    assert len(response_data) == 100

    # Assert that all experience IDs are unique
    assert len({experience["id"] for experience in response_data}) == len(response_data)

    # Assert experiences are sorted
    assert all(
        experience["id"] == str(experiences[i].id)
        for i, experience in enumerate(response_data)
    )

    # Assert the database still contains the same number of experiences
    experiences = db_session.exec(select(Experience)).all()
    assert len(experiences) == number_experiences


@pytest.mark.anyio
@pytest.mark.parametrize(
    "offset, limit, number_experiences",
    [
        (10, 100, 50),
        (0, 75, 100),
        (100, 75, 100),
        (100, 100, 200),
        (0, 0, 100),
        (50, 0, 10),
    ],
)
async def test_experiences_read_pagination(
    http_client: AsyncClient,
    db_session: Session,
    offset: int,
    limit: int,
    number_experiences: int,
):
    """Test the pagination behavior of retrieving experiences."""
    ExperienceFactory.__session__ = db_session

    # Create some experiences in the database
    ExperienceFactory.create_batch_sync(number_experiences)

    # Assert the expected number of experiences have been created
    experiences = db_session.exec(select(Experience)).all()
    assert len(experiences) == number_experiences

    # Get experiences with pagination
    response = await http_client.get(
        "/api/v1/experiences/", params={"offset": offset, "limit": limit}
    )
    response_data = response.json()
    assert response.status_code == 200

    # Assert that the number of experiences matches the pagination params
    expected_count = min(limit, max(0, number_experiences - offset))
    assert len(response_data) == expected_count

    # Assert that all experience IDs are unique
    assert len({experience["id"] for experience in response_data}) == len(response_data)

    # Assert experiences are sorted
    assert all(
        experience["id"] == str(experiences[i + offset].id)
        for i, experience in enumerate(response_data)
    )

    # Assert the database still contains the same number of experiences
    experiences = db_session.exec(select(Experience)).all()
    assert len(experiences) == number_experiences


@pytest.mark.anyio
@pytest.mark.parametrize(
    "invalid_params",
    [
        {"aggregation_level": 0, "structure": "atomic"},
        {"aggregation_level": 5},
        {"structure": "Atomic"},
        {"limit": 101},
        {"offset": -1},
    ],
)
async def test_experiences_read_invalid_params(
    http_client: AsyncClient, db_session: Session, invalid_params: dict
):
    """Test scenarios with invalid query parameters when retrieving experiences."""
    ExperienceFactory.__session__ = db_session

    # Create some experiences
    number_experiences = 10
    ExperienceFactory.create_batch_sync(10)

    # Read experiences with invalid query parameters
    response = await http_client.get("/api/v1/experiences/", params=invalid_params)

    # Assert the request fails
    assert response.status_code == 422

    # Assert the database still contains the same number of experiences
    experiences = db_session.exec(select(Experience)).all()
    assert len(experiences) == number_experiences


@pytest.mark.anyio
@pytest.mark.parametrize(
    "params, expected_count",
    [
        ({"aggregation_level": 1, "structure": "atomic"}, 25),
        ({"aggregation_level": 1}, 25),
        ({"structure": "hierarchical"}, 2),
        ({"structure": "collection"}, 12),
        ({"aggregation_level": 2}, 6),
        ({"aggregation_level": 3}, 8),
        ({"aggregation_level": 2, "structure": "hierarchical"}, 2),
        ({"aggregation_level": 3, "structure": "atomic"}, 0),
    ],
)
async def test_experiences_read_filter(
    http_client: AsyncClient, db_session: Session, params: dict, expected_count: int
):
    """Test scenarios with valid query parameters when retrieving experiences."""
    ExperienceFactory.__session__ = db_session

    # Attempt to retrieve experiences when the database is empty
    # with valid query parameters
    response = await http_client.get("/api/v1/experiences/", params=params)
    assert response.status_code == 200
    assert response.json() == []

    # Create four categories of experiences in the database
    ExperienceFactory.create_batch_sync(25, structure="atomic", aggregation_level=1)
    ExperienceFactory.create_batch_sync(
        2, structure="hierarchical", aggregation_level=2
    )
    ExperienceFactory.create_batch_sync(4, structure="collection", aggregation_level=2)
    ExperienceFactory.create_batch_sync(8, structure="collection", aggregation_level=3)

    # Read experiences with valid query parameters
    response = await http_client.get(
        "/api/v1/experiences/",
        params=params,
    )
    response_data = response.json()
    assert response.status_code == 200
    # Assert that the number of experiences matches the expected_count
    assert len(response_data) == expected_count

    # Assert that all experience IDs are unique
    assert len({experience["id"] for experience in response_data}) == expected_count

    # Assert the database still contains the same number of experiences
    experiences = db_session.exec(select(Experience)).all()
    assert len(experiences) == 39
