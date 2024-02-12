"""Tests for XI relations client."""

from unittest.mock import AsyncMock, call
from uuid import uuid4

import pytest
from httpx import AsyncClient, HTTPError
from pydantic.main import BaseModel
from sqlmodel import Session

from warren.xi.client import CRUDRelation
from warren.xi.enums import RelationType
from warren.xi.models import RelationCreate


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
