"""Tests for XI relations client."""

import re
from unittest.mock import AsyncMock, call
from uuid import uuid4

import pytest
from httpx import AsyncClient, HTTPError
from pydantic.main import BaseModel
from pytest_httpx import HTTPXMock
from sqlmodel import Session

from warren.xi.client import CRUDRelation
from warren.xi.enums import RelationType
from warren.xi.models import RelationCreate


@pytest.mark.anyio
async def test_crud_relation_raise_status(
    httpx_mock: HTTPXMock, http_client: AsyncClient
):
    """Test that each operation raises an HTTP error in case of failure."""
    crud_instance = CRUDRelation(client=http_client)

    # Mock each request to the XI by returning a 422 status
    httpx_mock.add_response(url=re.compile(r".*relations.*"), status_code=422)

    class WrongData(BaseModel):
        name: str

    # Assert 'create' raises an HTTP error
    with pytest.raises(HTTPError):
        await crud_instance.create(data=WrongData(name="foo"))

    # Assert 'update' raises an HTTP error
    with pytest.raises(HTTPError):
        await crud_instance.update(object_id=uuid4(), data=WrongData(name="foo"))

    # Assert 'read' raises an HTTP error
    with pytest.raises(HTTPError):
        await crud_instance.read()

    # Assert 'get' raises an HTTP error
    with pytest.raises(HTTPError):
        await crud_instance.get(object_id="foo.")


@pytest.mark.anyio
async def test_crud_relation_get_not_found(
    httpx_mock: HTTPXMock, http_client: AsyncClient
):
    """Test getting an unknown relation."""
    crud_instance = CRUDRelation(client=http_client)

    # Mock GET request to the XI by returning a 404 status
    httpx_mock.add_response(
        method="GET", url=re.compile(r".*relations.*"), status_code=404
    )

    # Assert 'get' return 'None' without raising any HTTP errors
    response = await crud_instance.get(object_id=uuid4())
    assert response is None


@pytest.mark.anyio
async def test_crud_relation_create_bidirectional(
    http_client: AsyncClient, db_session: Session
):
    """Test creating bidirectional relations."""
    crud_instance = CRUDRelation(client=http_client)

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
