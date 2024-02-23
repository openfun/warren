"""Tests for XI relations client."""

from unittest.mock import AsyncMock, call
from uuid import uuid4

import pytest
from httpx import AsyncClient, HTTPError
from pydantic.main import BaseModel
from sqlmodel import Session

from warren.xi.client import CRUDRelation
from warren.xi.enums import RelationType
from warren.xi.factories import RelationFactory
from warren.xi.models import RelationCreate, RelationRead, RelationUpdate


@pytest.mark.anyio
async def test_crud_relation_raise_status(http_auth_client: AsyncClient, monkeypatch):
    """Test that each operation raises an HTTP error in case of failure."""
    monkeypatch.setattr(CRUDRelation, "_base_url", "/api/v1/relations")
    crud_instance = CRUDRelation(client=http_auth_client)

    class WrongData(BaseModel):
        name: str

    # Assert 'create' raises an HTTP error
    with pytest.raises(HTTPError, match="422"):
        await crud_instance.create(data=WrongData(name="foo"))

    # Assert 'update' raises an HTTP error
    with pytest.raises(HTTPError, match="404"):
        await crud_instance.update(object_id=uuid4(), data=WrongData(name="foo"))

    # Assert 'get' raises an HTTP error
    with pytest.raises(HTTPError, match="422"):
        await crud_instance.get(object_id="foo.")


@pytest.mark.anyio
async def test_crud_relation_create(
    http_auth_client: AsyncClient, db_session: Session, monkeypatch
):
    """Test we are able to create a new relation."""
    RelationFactory.__session__ = db_session
    monkeypatch.setattr(CRUDRelation, "_base_url", "/api/v1/relations")
    crud_instance = CRUDRelation(client=http_auth_client)

    relation = RelationFactory.build()
    relation_read = await crud_instance.create(RelationCreate(**relation.dict()))

    expected = RelationRead(**relation.dict())
    exclude = {
        "id",
        "created_at",
        "updated_at",
    }
    cmp_options = {"exclude": exclude}
    assert relation_read.dict(**cmp_options) == expected.dict(**cmp_options)


@pytest.mark.anyio
async def test_crud_relation_get(
    http_auth_client: AsyncClient, db_session: Session, monkeypatch
):
    """Test we are able to get a relation."""
    RelationFactory.__session__ = db_session
    monkeypatch.setattr(CRUDRelation, "_base_url", "/api/v1/relations")
    crud_instance = CRUDRelation(client=http_auth_client)

    # Create a relation object but don't save it to database
    # so that it's not expected to exists
    relation = RelationFactory.build()
    relation_read = await crud_instance.get(object_id=relation.id)
    assert relation_read is None

    # Now save a new relation and try to get it by its ID
    relation = RelationFactory.create_sync()
    relation_read = await crud_instance.get(object_id=relation.id)
    expected = RelationRead(**relation.dict())
    exclude = {
        "created_at",
        "updated_at",
    }
    cmp_options = {"exclude": exclude}
    assert relation_read.dict(**cmp_options) == expected.dict(**cmp_options)


@pytest.mark.anyio
async def test_crud_relation_get_not_found(http_auth_client: AsyncClient, monkeypatch):
    """Test getting an unknown relation."""
    monkeypatch.setattr(CRUDRelation, "_base_url", "/api/v1/relations")
    crud_instance = CRUDRelation(client=http_auth_client)

    # Assert 'get' return 'None' without raising any HTTP errors
    response = await crud_instance.get(object_id=uuid4())
    assert response is None


@pytest.mark.anyio
async def test_crud_relation_read_empty(http_auth_client: AsyncClient, monkeypatch):
    """Test reading relations when no relation has been saved."""
    monkeypatch.setattr(CRUDRelation, "_base_url", "/api/v1/relations")
    crud_instance = CRUDRelation(client=http_auth_client)

    # Assert 'get' return 'None' without raising any HTTP errors
    relations = await crud_instance.read()
    assert relations == []


@pytest.mark.anyio
async def test_crud_relation_update(
    http_auth_client: AsyncClient, db_session: Session, monkeypatch
):
    """Test we are able to update a relation."""
    RelationFactory.__session__ = db_session
    monkeypatch.setattr(CRUDRelation, "_base_url", "/api/v1/relations")
    crud_instance = CRUDRelation(client=http_auth_client)

    # Save a new relation to update
    relation = RelationFactory.create_sync(kind=RelationType.ISPARTOF)
    assert (
        await crud_instance.get(object_id=relation.id)
    ).kind == RelationType.ISPARTOF

    # Update
    relation_update = await crud_instance.update(
        object_id=relation.id, data=RelationUpdate(kind=RelationType.HASPART)
    )
    assert relation_update.kind == RelationType.HASPART
    assert (await crud_instance.get(object_id=relation.id)).kind == RelationType.HASPART


@pytest.mark.anyio
async def test_crud_relation_delete(
    http_auth_client: AsyncClient, db_session: Session, monkeypatch
):
    """Test we are not able to delete a relation using the client."""
    RelationFactory.__session__ = db_session
    monkeypatch.setattr(CRUDRelation, "_base_url", "/api/v1/relations")
    crud_instance = CRUDRelation(client=http_auth_client)

    with pytest.raises(NotImplementedError):
        await crud_instance.delete()


@pytest.mark.anyio
async def test_crud_relation_create_or_update_new(
    http_auth_client: AsyncClient, db_session: Session, monkeypatch
):
    """Test creating a relation using 'create_or_update'."""
    RelationFactory.__session__ = db_session
    monkeypatch.setattr(CRUDRelation, "_base_url", "/api/v1/relations")
    crud_instance = CRUDRelation(client=http_auth_client)

    # Get random experience data
    data = RelationFactory.build()

    # Simulate a 'Not Found' experience by mocking the 'get' method
    crud_instance.read = AsyncMock(return_value=None)

    crud_instance.create = AsyncMock()
    crud_instance.update = AsyncMock()

    # Attempt creating an experience
    await crud_instance.create_or_update(RelationCreate(**data.dict()))

    crud_instance.create.assert_awaited_once()
    crud_instance.update.assert_not_awaited()


@pytest.mark.anyio
async def test_crud_relation_create_or_update_existing(
    http_auth_client: AsyncClient, db_session: Session, monkeypatch
):
    """Test updating a relation using 'create_or_update'."""
    RelationFactory.__session__ = db_session
    monkeypatch.setattr(CRUDRelation, "_base_url", "/api/v1/relations")
    crud_instance = CRUDRelation(client=http_auth_client)

    # Get random experience data
    data = RelationFactory.build()

    # Simulate an existing relation by mocking the 'get' method
    crud_instance.read = AsyncMock(return_value=[RelationRead(**data.dict())])

    crud_instance.create = AsyncMock()
    crud_instance.update = AsyncMock()

    # Attempt creating an experience
    await crud_instance.create_or_update(RelationCreate(**data.dict()))

    crud_instance.create.assert_not_awaited()
    crud_instance.update.assert_awaited_once()


@pytest.mark.anyio
async def test_crud_relation_create_bidirectional(
    http_auth_client: AsyncClient, db_session: Session, monkeypatch
):
    """Test creating bidirectional relations."""
    monkeypatch.setattr(CRUDRelation, "_base_url", "/api/v1/relations")
    crud_instance = CRUDRelation(client=http_auth_client)

    # Get two inverse relation types
    relation_type = RelationType.HASPART
    inverted_relation_type = RelationType.ISPARTOF

    # Get two random UUIDs
    source_id = uuid4()
    target_id = uuid4()

    # Mock 'create' method by returning a random UUID
    crud_instance.create = AsyncMock(return_value=uuid4())

    # Attempt creating bidirectional relations
    _ = await crud_instance.create_bidirectional(
        source_id=source_id,
        target_id=target_id,
        kinds=[relation_type, inverted_relation_type],
    )

    # Assert 'create' has been called twice, with inverted arguments
    crud_instance.create.assert_has_awaits(
        [
            call(
                RelationCreate(
                    source_id=source_id, target_id=target_id, kind=relation_type
                )
            ),
            call(
                RelationCreate(
                    source_id=target_id,
                    target_id=source_id,
                    kind=inverted_relation_type,
                )
            ),
        ]
    )
