"""Tests for the experience index API '/relation' endpoints."""

# ruff: noqa: S311

from datetime import timezone
from uuid import uuid4

import pytest
from freezegun import freeze_time
from httpx import AsyncClient
from sqlmodel import Session, select

from warren.xi.enums import RelationType
from warren.xi.factories import (
    ExperienceFactory,
    RelationFactory,
)
from warren.xi.schema import Experience, Relation


@pytest.mark.anyio
async def test_relation_auth(http_client: AsyncClient):
    """Test required authentication for relation endpoints."""
    assert (await http_client.get("/api/v1/relations/")).status_code == 401
    assert (await http_client.post("/api/v1/relations/", json={})).status_code == 401
    assert (await http_client.get("/api/v1/relations/foo")).status_code == 401
    assert (await http_client.put("/api/v1/relations/foo", json={})).status_code == 401


@pytest.mark.anyio
async def test_relation_read(
    http_client: AsyncClient, auth_headers: dict, db_session: Session
):
    """Test retrieving detailed information about a relation."""
    RelationFactory.__session__ = db_session

    # Create a relation in the database
    time = RelationFactory.__faker__.date_time(timezone.utc).isoformat()
    with freeze_time(time):
        relation = RelationFactory.create_sync()

    # Attempt to read the last created relation
    response = await http_client.get(
        f"/api/v1/relations/{relation.id}",
        headers=auth_headers,
    )
    assert response.status_code == 200

    # Verify the retrieved data matches the expected format
    assert response.json() == {
        "id": str(relation.id),
        "created_at": time,
        "updated_at": time,
        "source_id": str(relation.source_id),
        "target_id": str(relation.target_id),
        "kind": relation.kind,
    }

    # Assert the database contains one relation
    relations = db_session.exec(select(Relation)).all()
    assert len(relations) == 1


@pytest.mark.anyio
@pytest.mark.parametrize("invalid_id", ["foo", 123, "a1-a2-aa", uuid4().hex + "a"])
async def test_relation_read_invalid(
    http_client: AsyncClient, auth_headers: dict, db_session: Session, invalid_id: any
):
    """Test retrieving a relation with an invalid or nonexistent ID."""
    RelationFactory.__session__ = db_session

    # Create some relations in the database
    number_relations = 10
    RelationFactory.create_batch_sync(number_relations)

    # Attempt to read a relation with an invalid ID
    response = await http_client.get(
        f"/api/v1/relations/{invalid_id}",
        headers=auth_headers,
    )
    assert response.status_code == 422

    # Attempt to read a relation with a nonexistent ID
    nonexistent_id = uuid4().hex
    response = await http_client.get(
        f"/api/v1/relations/{nonexistent_id}",
        headers=auth_headers,
    )
    assert response.status_code == 404
    assert response.json() == {"detail": "Relation not found"}

    # Assert the database still contains the same number of relations
    relations = db_session.exec(select(Relation)).all()
    assert len(relations) == number_relations


@pytest.mark.anyio
async def test_relations_read_default(
    http_client: AsyncClient, auth_headers: dict, db_session: Session
):
    """Test the default behavior of retrieving relations."""
    RelationFactory.__session__ = db_session

    # Create some relations in the database
    number_relations = 200
    RelationFactory.create_batch_sync(number_relations)

    relations = db_session.exec(select(Relation)).all()

    # Retrieve relations without any query parameters
    response = await http_client.get(
        "/api/v1/relations/",
        headers=auth_headers,
    )
    response_data = response.json()
    assert response.status_code == 200

    # Assert that the number of relations matches the default limit (100)
    assert len(response_data) == 100

    # Assert that all relations IDs are unique
    assert len({relation["id"] for relation in response_data}) == len(response_data)

    # Assert relations are sorted
    assert all(
        relation["id"] == str(relations[i].id)
        for i, relation in enumerate(response_data)
    )

    # Assert the database still contains the same number of relations
    relations = db_session.exec(select(Relation)).all()
    assert len(relations) == number_relations


@pytest.mark.anyio
@pytest.mark.parametrize(
    "offset, limit, number_relations",
    [
        (10, 100, 50),
        (0, 75, 100),
        (100, 75, 100),
        (100, 100, 200),
        (0, 0, 100),
        (50, 0, 10),
    ],
)
async def test_relations_read_pagination(
    http_client: AsyncClient,
    auth_headers: dict,
    db_session: Session,
    offset: int,
    limit: int,
    number_relations: int,
):
    """Test the pagination behavior of retrieving relations."""
    RelationFactory.__session__ = db_session

    # Create some relations in the database
    RelationFactory.create_batch_sync(number_relations)

    relations = db_session.exec(select(Relation)).all()
    assert len(relations) == number_relations

    # Get relations with pagination
    response = await http_client.get(
        "/api/v1/relations/",
        headers=auth_headers,
        params={"offset": offset, "limit": limit},
    )
    response_data = response.json()
    assert response.status_code == 200

    # Assert that the number of relations matches the pagination params
    expected_count = min(limit, max(0, number_relations - offset))
    assert len(response_data) == expected_count

    # Assert that all relations IDs are unique
    assert len({relation["id"] for relation in response_data}) == len(response_data)

    # Assert relations are sorted
    assert all(
        relation["id"] == str(relations[i + offset].id)
        for i, relation in enumerate(response_data)
    )

    # Assert the database still contains the same number of relations
    relations = db_session.exec(select(Relation)).all()
    assert len(relations) == number_relations


@pytest.mark.anyio
@pytest.mark.parametrize(
    "invalid_params",
    [
        {"limit": 101},
        {"offset": -1},
        {"offset": "a"},
        {"limit": "b"},
    ],
)
async def test_relations_read_invalid_params(
    http_client: AsyncClient,
    auth_headers: dict,
    db_session: Session,
    invalid_params: dict,
):
    """Test scenarios with invalid query parameters when retrieving relations."""
    RelationFactory.__session__ = db_session

    # Create some relations in the database
    number_relations = 10
    RelationFactory.create_batch_sync(number_relations)

    # Read relations with invalid query parameters
    response = await http_client.get(
        "/api/v1/relations/", headers=auth_headers, params=invalid_params
    )

    # Assert the request fails
    assert response.status_code == 422

    # Assert the database still contains the same number of relations
    relations = db_session.exec(select(Relation)).all()
    assert len(relations) == number_relations


@pytest.mark.anyio
async def test_relation_create(
    http_client: AsyncClient, auth_headers: dict, db_session: Session
):
    """Test creating a relation with valid data."""
    ExperienceFactory.__session__ = db_session

    # Create two experiences in the database
    source, target = ExperienceFactory.create_batch_sync(2)

    relation_type = ExperienceFactory.__random__.choice(list(RelationType))

    # Attempt creating a relation with valid data
    time = ExperienceFactory.__faker__.date_time(timezone.utc).isoformat()
    with freeze_time(time):
        response = await http_client.post(
            "/api/v1/relations/",
            headers=auth_headers,
            json={
                "source_id": str(source.id),
                "target_id": str(target.id),
                "kind": relation_type,
            },
        )
        response_data = response.json()

    assert response.status_code == 200

    # Declare the expected relation saved in the database
    expected_relation = Relation(
        id=response_data,
        source_id=source.id,
        target_id=target.id,
        kind=relation_type,
        created_at=time,
        updated_at=time,
    )

    # Assert that the relation has been correctly saved
    assert db_session.get(Relation, response_data) == expected_relation

    db_session.refresh(source)
    db_session.refresh(target)

    # Assert source experience has the new relation
    assert source.relations_source == [expected_relation]
    assert source.relations_target == []

    # Assert target experience has the new relation
    assert target.relations_source == []
    assert target.relations_target == [expected_relation]

    # Assert the database contains one relation
    relations = db_session.exec(select(Relation)).all()
    assert len(relations) == 1


@pytest.mark.anyio
async def test_relation_create_multiple(
    http_client: AsyncClient, auth_headers: dict, db_session: Session
):
    """Test creating multiple relations with valid data."""
    ExperienceFactory.__session__ = db_session

    for n in range(1, 10):
        # Create two experiences in the database
        source, target = ExperienceFactory.create_batch_sync(2)

        relation_type = ExperienceFactory.__random__.choice(list(RelationType))

        # Attempt creating a relation with valid data
        time = ExperienceFactory.__faker__.date_time(timezone.utc).isoformat()
        with freeze_time(time):
            response = await http_client.post(
                "/api/v1/relations/",
                headers=auth_headers,
                json={
                    "source_id": str(source.id),
                    "target_id": str(target.id),
                    "kind": relation_type,
                },
            )
            response_data = response.json()

        assert response.status_code == 200

        # Declare the expected relation saved in the database
        expected_relation = Relation(
            id=response_data,
            source_id=source.id,
            target_id=target.id,
            kind=relation_type,
            created_at=time,
            updated_at=time,
        )

        # Assert that the relation has been correctly saved
        assert db_session.get(Relation, response_data) == expected_relation

        db_session.refresh(source)
        db_session.refresh(target)

        # Assert source experience has the new relation
        assert source.relations_source == [expected_relation]
        assert source.relations_target == []

        # Assert target experience has the new relation
        assert target.relations_source == []
        assert target.relations_target == [expected_relation]

        # Assert the database contains one relation
        relations = db_session.exec(select(Relation)).all()
        assert len(relations) == n


@pytest.mark.anyio
async def test_relation_create_empty(
    http_client: AsyncClient, auth_headers: dict, db_session: Session
):
    """Test creating an empty relation."""
    # Attempt to create an empty relation
    response = await http_client.post(
        "/api/v1/relations/", headers=auth_headers, json={}
    )

    # Relation's creation should fail
    assert response.status_code == 422

    # Assert the database is empty
    relations = db_session.exec(select(Relation)).all()
    assert len(relations) == 0


@pytest.mark.anyio
@pytest.mark.parametrize(
    "invalid_data",
    [
        {"kind": 12},
        {"source_id": "foo."},
        {"target_id": -1, "kind": 12},
        {"target_id": "a" * 200},
    ],
)
async def test_relation_create_invalid(
    http_client: AsyncClient,
    auth_headers: dict,
    db_session: Session,
    invalid_data: dict,
):
    """Test creating a relation with invalid data."""
    # Valid data for creating a relation
    base_data = {
        "source_id": uuid4().hex,
        "target_id": uuid4().hex,
        "kind": ExperienceFactory.__random__.choice(list(RelationType)),
    }

    # Create a relation with invalid data
    response = await http_client.post(
        "/api/v1/relations/",
        headers=auth_headers,
        json={**base_data, **invalid_data},
    )
    assert response.status_code == 422

    # Assert the database is empty
    relations = db_session.exec(select(Relation)).all()
    assert len(relations) == 0


@pytest.mark.anyio
async def test_relation_create_nonexistent_target(
    http_client: AsyncClient, auth_headers: dict, db_session: Session
):
    """Test creating a relation with a nonexistent target experience."""
    ExperienceFactory.__session__ = db_session

    # Create one experience in the database
    source = ExperienceFactory.create_sync()

    # Declare an id that does not exist in the database
    nonexistent_id = uuid4().hex

    # Attempt creating a relation between existing and nonexistent experiences
    response = await http_client.post(
        "/api/v1/relations/",
        headers=auth_headers,
        json={
            "source_id": str(source.id),
            "target_id": nonexistent_id,
            "kind": ExperienceFactory.__random__.choice(list(RelationType)),
        },
    )
    assert response.status_code == 500
    assert response.json() == {
        "detail": "An error occurred while creating the relation"
    }


@pytest.mark.anyio
async def test_relation_create_nonexistent_source(
    http_client: AsyncClient, auth_headers: dict, db_session: Session
):
    """Test creating a relation with a nonexistent source experience."""
    ExperienceFactory.__session__ = db_session

    # Create one experience in the database
    target = ExperienceFactory.create_sync()

    # Declare an id that does not exist in the database
    nonexistent_id = uuid4().hex

    # Attempt creating a relation between existing and nonexistent experiences
    response = await http_client.post(
        "/api/v1/relations/",
        headers=auth_headers,
        json={
            "source_id": nonexistent_id,
            "target_id": str(target.id),
            "kind": ExperienceFactory.__random__.choice(list(RelationType)),
        },
    )
    assert response.status_code == 500
    assert response.json() == {
        "detail": "An error occurred while creating the relation"
    }


@pytest.mark.anyio
async def test_relation_create_nonexistent_source_and_target(
    http_client: AsyncClient,
    auth_headers: dict,
):
    """Test creating a relation with nonexistent source and target experiences."""
    # Attempt creating a relation between nonexistent experiences
    response = await http_client.post(
        "/api/v1/relations/",
        headers=auth_headers,
        json={
            "source_id": uuid4().hex,
            "target_id": uuid4().hex,
            "kind": ExperienceFactory.__random__.choice(list(RelationType)),
        },
    )
    assert response.status_code == 500
    assert response.json() == {
        "detail": "An error occurred while creating the relation"
    }


@pytest.mark.anyio
async def test_relation_create_bidirectional(
    http_client: AsyncClient, auth_headers: dict, db_session: Session
):
    """Test creating bidirectional relations between source and target experiences."""
    RelationFactory.__session__ = db_session

    # Create relation data, with experiences saved in the database
    relation = RelationFactory.build()

    # Attempt creating the relation pointing from source to target
    time = RelationFactory.__faker__.date_time(timezone.utc).isoformat()
    with freeze_time(time):
        response = await http_client.post(
            "/api/v1/relations/",
            headers=auth_headers,
            json={
                "source_id": str(relation.source_id),
                "target_id": str(relation.target_id),
                "kind": relation.kind,
            },
        )
        response_data = response.json()

    assert response.status_code == 200

    # Get the saved experiences in the database
    source = db_session.get(Experience, relation.source_id)
    target = db_session.get(Experience, relation.target_id)

    # Declare the expected relation saved in the database
    relation_source_to_target = Relation(
        id=response_data,
        source_id=source.id,
        target_id=target.id,
        kind=relation.kind,
        created_at=time,
        updated_at=time,
    )

    # Verify that the relation has been correctly saved
    assert db_session.get(Relation, response_data) == relation_source_to_target

    # Assert source experience has the new relation
    assert source.relations_source == [relation_source_to_target]
    assert source.relations_target == []

    # Assert target experience has the new relation
    assert target.relations_source == []
    assert target.relations_target == [relation_source_to_target]

    # Attempt creating the relation pointing from target to source
    time = RelationFactory.__faker__.date_time(timezone.utc).isoformat()
    with freeze_time(time):
        response = await http_client.post(
            "/api/v1/relations/",
            headers=auth_headers,
            json={
                "source_id": str(target.id),
                "target_id": str(source.id),
                "kind": relation.kind,
            },
        )
        response_data = response.json()

    assert response.status_code == 200

    # Declare the expected relation saved in the database
    relation_target_to_source = Relation(
        id=response_data,
        source_id=target.id,
        target_id=source.id,
        kind=relation.kind,
        created_at=time,
        updated_at=time,
    )

    # Verify that the relation has been correctly saved
    assert db_session.get(Relation, response_data) == relation_target_to_source

    db_session.refresh(source)
    db_session.refresh(target)

    # Assert source experience has both relations
    assert source.relations_source == [relation_source_to_target]
    assert source.relations_target == [relation_target_to_source]

    # Assert target experience has both relations
    assert target.relations_source == [relation_target_to_source]
    assert target.relations_target == [relation_source_to_target]

    # Assert the database contains two relations
    relations = db_session.exec(select(Relation)).all()
    assert len(relations) == 2


@pytest.mark.anyio
async def test_relation_create_self_referential(
    http_client: AsyncClient, auth_headers: dict, db_session: Session
):
    """Test creating a self-referential relation on a single experience."""
    RelationFactory.__session__ = db_session

    # Create one experience in the database
    relation = RelationFactory.build()
    experience_id = str(relation.source_id)

    # Attempt creating a self-referential relation
    response = await http_client.post(
        "/api/v1/relations/",
        headers=auth_headers,
        json={
            "source_id": experience_id,
            "target_id": experience_id,
            "kind": relation.kind,
        },
    )
    assert response.status_code == 500
    assert response.json() == {
        "detail": "An error occurred while creating the relation"
    }


@pytest.mark.anyio
async def test_relation_create_duplicated(
    http_client: AsyncClient, auth_headers: dict, db_session: Session
):
    """Test creating a duplicated relation between source and target experiences."""
    RelationFactory.__session__ = db_session

    # Create a relation in the database
    relation = RelationFactory.create_sync()

    # Attempt creating a duplicated relation
    response = await http_client.post(
        "/api/v1/relations/",
        headers=auth_headers,
        json={
            "source_id": str(relation.source_id),
            "target_id": str(relation.target_id),
            "kind": relation.kind,
        },
    )
    assert response.status_code == 500
    assert response.json() == {
        "detail": "An error occurred while creating the relation"
    }


@pytest.mark.anyio
async def test_relation_update(
    http_client: AsyncClient, auth_headers: dict, db_session: Session
):
    """Test updating a relation with a single update scenario."""
    ExperienceFactory.__session__ = RelationFactory.__session__ = db_session

    # Create three experiences in the database
    (
        experience_one,
        experience_two,
        experience_three,
    ) = ExperienceFactory.create_batch_sync(3)

    # Create a relation between these experiences in the database
    creation_date = RelationFactory.__faker__.date_time(timezone.utc)
    update_date = RelationFactory.__faker__.date_time_between(
        creation_date, tzinfo=timezone.utc
    )
    with freeze_time(creation_date):
        relation = RelationFactory.create_sync(
            source_id=experience_one.id,
            target_id=experience_two.id,
        )

    # Attempt updating the created relation
    relation_type = ExperienceFactory.__random__.choice(list(RelationType))
    with freeze_time(update_date):
        response = await http_client.put(
            f"/api/v1/relations/{relation.id}",
            headers=auth_headers,
            json={
                "source_id": str(experience_three.id),
                "target_id": str(experience_one.id),
                "kind": relation_type,
            },
        )

    assert response.status_code == 200

    # Assert the relation has been updated
    assert db_session.get(Relation, relation.id) == Relation(
        id=str(relation.id),
        source_id=str(experience_three.id),
        target_id=str(experience_one.id),
        kind=relation_type,
        created_at=creation_date.isoformat(),
        updated_at=update_date.isoformat(),
    )

    # Assert the database contains one relation
    relations = db_session.exec(select(Relation)).all()
    assert len(relations) == 1


@pytest.mark.anyio
async def test_relation_update_empty(
    http_client: AsyncClient, auth_headers: dict, db_session: Session
):
    """Test updating a relation with empty data."""
    RelationFactory.__session__ = db_session

    # Create a relation in the database
    creation_date = RelationFactory.__faker__.date_time(timezone.utc)
    update_date = ExperienceFactory.__faker__.date_time_between(
        creation_date, tzinfo=timezone.utc
    )
    with freeze_time(creation_date):
        relation = RelationFactory.create_sync()

    # Attempt updating the created relation with no data
    with freeze_time(update_date):
        response = await http_client.put(
            f"/api/v1/relations/{relation.id}",
            headers=auth_headers,
            json={},
        )
    assert response.status_code == 200

    # Assert the relation has not been updated
    assert db_session.get(Relation, relation.id) == Relation(
        id=str(relation.id),
        source_id=str(relation.source_id),
        target_id=str(relation.target_id),
        kind=relation.kind,
        created_at=creation_date.isoformat(),
        updated_at=creation_date.isoformat(),
    )

    # Assert the database contains one relation
    relations = db_session.exec(select(Relation)).all()
    assert len(relations) == 1


@pytest.mark.anyio
@pytest.mark.parametrize(
    "invalid_data",
    [
        {"kind": 12},
        {"source_id": "foo."},
        {"target_id": -1, "kind": 12},
        {"target_id": "a" * 200},
    ],
)
async def test_relation_update_invalid(
    http_client: AsyncClient,
    auth_headers: dict,
    db_session: Session,
    invalid_data: dict,
):
    """Test updating a relation with invalid data."""
    RelationFactory.__session__ = db_session

    # Create source and target experiences in the database
    relation = RelationFactory.create_sync()

    # Attempt updating a nonexistent relation
    wrong_id = uuid4().hex
    response = await http_client.put(
        f"/api/v1/relations/{wrong_id}",
        headers=auth_headers,
        json={},
    )
    assert response.status_code == 404
    assert response.json() == {"detail": "Relation not found"}

    # Attempt updating the relation with invalid data
    response = await http_client.put(
        f"/api/v1/relations/{relation.id}",
        headers=auth_headers,
        json=invalid_data,
    )
    assert response.status_code == 422

    # Assert the database contains one relation
    relations = db_session.exec(select(Relation)).all()
    assert len(relations) == 1


@pytest.mark.anyio
async def test_relation_update_self_referential(
    http_client: AsyncClient, auth_headers: dict, db_session: Session
):
    """Test updating a relation to a self-referential relation."""
    ExperienceFactory.__session__ = RelationFactory.__session__ = db_session

    # Create a relation in the database
    relation = RelationFactory.create_sync()

    # Attempt updating the relation to a self-referential relation
    response = await http_client.put(
        f"/api/v1/relations/{relation.id}",
        headers=auth_headers,
        json={
            "source_id": str(relation.source_id),
            "target_id": str(relation.source_id),
        },
    )
    assert response.status_code == 500
    assert response.json() == {
        "detail": "An error occurred while updating the relation"
    }


@pytest.mark.anyio
async def test_relation_update_duplicated(
    http_client: AsyncClient, auth_headers: dict, db_session: Session
):
    """Test updating a relation with duplicated data."""
    RelationFactory.__session__ = db_session

    # Create a first relation in the database
    first_relation = RelationFactory.create_sync()

    # Exclude first relation's value before creating a second one
    available_kind_values = list(RelationType)
    available_kind_values.remove(first_relation.kind)

    # Create a second relation in the database between the same experiences
    second_relation = RelationFactory.create_sync(
        source_id=first_relation.source_id,
        target_id=first_relation.target_id,
        kind=ExperienceFactory.__random__.choice(available_kind_values),
    )

    # Attempt updating the second relation to be equal to the first one
    response = await http_client.put(
        f"/api/v1/relations/{second_relation.id}",
        headers=auth_headers,
        json={"kind": first_relation.kind},
    )
    assert response.status_code == 500
    assert response.json() == {
        "detail": "An error occurred while updating the relation"
    }


@pytest.mark.anyio
async def test_relation_update_nonexistent_source(
    http_client: AsyncClient, auth_headers: dict, db_session: Session
):
    """Test updating a relation with a nonexistent source."""
    RelationFactory.__session__ = db_session

    # Create a relation in the database
    relation = RelationFactory.create_sync()

    # Declare an id that does not exist in the database
    nonexistent_id = uuid4().hex

    # Attempt updating the relation with a nonexistent source
    response = await http_client.put(
        f"/api/v1/relations/{relation.id}",
        headers=auth_headers,
        json={"source_id": nonexistent_id},
    )
    assert response.status_code == 500
    assert response.json() == {
        "detail": "An error occurred while updating the relation"
    }


@pytest.mark.anyio
async def test_relation_update_nonexistent_target(
    http_client: AsyncClient, auth_headers: dict, db_session: Session
):
    """Test updating a relation with a nonexistent target."""
    RelationFactory.__session__ = db_session

    # Create a relation in the database
    relation = RelationFactory.create_sync()

    # Declare an id that does not exist in the database
    nonexistent_id = uuid4().hex

    # Attempt updating the relation with a nonexistent target
    response = await http_client.put(
        f"/api/v1/relations/{relation.id}",
        headers=auth_headers,
        json={"target_id": nonexistent_id},
    )
    assert response.status_code == 500
    assert response.json() == {
        "detail": "An error occurred while updating the relation"
    }
