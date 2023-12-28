"""Tests for XI experiences client."""

import re
import uuid
from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient, HTTPError
from pydantic.main import BaseModel
from pytest_httpx import HTTPXMock
from sqlmodel import Session

from warren.xi.client import CRUDExperience
from warren.xi.factories import ExperienceFactory
from warren.xi.models import ExperienceCreate, ExperienceRead


@pytest.mark.anyio
async def test_crud_experience_raise_status(
    httpx_mock: HTTPXMock, http_client: AsyncClient
):
    """Test that each operation raises an HTTP error in case of failure."""
    crud_instance = CRUDExperience(client=http_client)

    # Mock each request to the XI by returning a 422 status
    httpx_mock.add_response(url=re.compile(r".*experiences.*"), status_code=422)

    class WrongData(BaseModel):
        name: str

    # Assert 'create' raises an HTTP error
    with pytest.raises(HTTPError):
        await crud_instance.create(data=WrongData(name="foo"))

    # Assert 'update' raises an HTTP error
    with pytest.raises(HTTPError):
        await crud_instance.update(object_id=uuid.uuid4(), data=WrongData(name="foo"))

    # Assert 'read' raises an HTTP error
    with pytest.raises(HTTPError):
        await crud_instance.read()

    # Assert 'get' raises an HTTP error
    with pytest.raises(HTTPError):
        await crud_instance.get(object_id="foo.")


@pytest.mark.anyio
async def test_crud_experience_get_not_found(
    httpx_mock: HTTPXMock, http_client: AsyncClient
):
    """Test getting an unknown experience."""
    crud_instance = CRUDExperience(client=http_client)

    # Mock GET request to the XI by returning a 404 status
    httpx_mock.add_response(
        method="GET", url=re.compile(r".*experiences.*"), status_code=404
    )

    # Assert 'get' return 'None' without raising any HTTP errors
    response = await crud_instance.get(object_id=uuid.uuid4())
    assert response is None


@pytest.mark.anyio
async def test_crud_experience_create_or_update_new(
    http_client: AsyncClient, db_session: Session
):
    """Test creating an experience using 'create_or_update'."""
    crud_instance = CRUDExperience(client=http_client)

    # Get random experience data
    data = ExperienceFactory.build_dict()

    # Simulate a 'Not Found' experience by mocking the 'get' method
    crud_instance.get = AsyncMock(return_value=None)

    crud_instance.create = AsyncMock()
    crud_instance.update = AsyncMock()

    # Attempt creating an experience
    await crud_instance.create_or_update(ExperienceCreate(**data))

    crud_instance.create.assert_awaited_once()
    crud_instance.update.assert_not_awaited()


@pytest.mark.anyio
async def test_crud_experience_create_or_update_existing(
    http_client: AsyncClient, db_session: Session
):
    """Test updating an experience using 'create_or_update'."""
    crud_instance = CRUDExperience(client=http_client)

    # Get random experience data
    data = ExperienceFactory.build_dict(exclude={})

    # Simulate an existing experience by mocking the 'get' method
    crud_instance.get = AsyncMock(return_value=ExperienceRead(**data))

    crud_instance.create = AsyncMock()
    crud_instance.update = AsyncMock()

    # Attempt updating an experience
    await crud_instance.create_or_update(ExperienceCreate(**data))

    crud_instance.create.assert_not_awaited()
    crud_instance.update.assert_awaited_once()
