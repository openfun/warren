"""Tests for XI experiences client."""

import uuid
from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient, HTTPError
from pydantic.main import BaseModel
from sqlmodel import Session

from warren.xi.client import CRUDExperience
from warren.xi.factories import ExperienceFactory
from warren.xi.models import ExperienceCreate, ExperienceRead


@pytest.mark.anyio
async def test_crud_experience_raise_status(http_auth_client: AsyncClient, monkeypatch):
    """Test that each operation raises an HTTP error in case of failure."""
    monkeypatch.setattr(CRUDExperience, "_base_url", "/api/v1/experiences")
    crud_instance = CRUDExperience(client=http_auth_client)

    class WrongData(BaseModel):
        name: str

    # Assert 'create' raises an HTTP error
    with pytest.raises(HTTPError, match="422"):
        await crud_instance.create(data=WrongData(name="foo"))

    # Assert 'update' raises an HTTP error
    with pytest.raises(HTTPError, match="404"):
        await crud_instance.update(object_id=uuid.uuid4(), data=WrongData(name="foo"))

    # Assert 'get' raises an HTTP error
    with pytest.raises(HTTPError, match="422"):
        await crud_instance.get(object_id="foo.")


@pytest.mark.anyio
async def test_crud_experience_get_not_found(
    http_auth_client: AsyncClient, monkeypatch
):
    """Test getting an unknown experience."""
    monkeypatch.setattr(CRUDExperience, "_base_url", "/api/v1/experiences")
    crud_instance = CRUDExperience(client=http_auth_client)

    # Assert 'get' return 'None' without raising any HTTP errors
    response = await crud_instance.get(object_id=uuid.uuid4())
    assert response is None


@pytest.mark.anyio
async def test_crud_experience_read_empty(http_auth_client: AsyncClient, monkeypatch):
    """Test reading experiences when no experience has been saved."""
    monkeypatch.setattr(CRUDExperience, "_base_url", "/api/v1/experiences")
    crud_instance = CRUDExperience(client=http_auth_client)

    # Assert 'get' return 'None' without raising any HTTP errors
    experiences = await crud_instance.read()
    assert experiences == []


@pytest.mark.anyio
async def test_crud_experience_create_or_update_new(
    http_auth_client: AsyncClient, db_session: Session, monkeypatch
):
    """Test creating an experience using 'create_or_update'."""
    monkeypatch.setattr(CRUDExperience, "_base_url", "/api/v1/experiences")
    crud_instance = CRUDExperience(client=http_auth_client)

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
    http_auth_client: AsyncClient, db_session: Session, monkeypatch
):
    """Test updating an experience using 'create_or_update'."""
    monkeypatch.setattr(CRUDExperience, "_base_url", "/api/v1/experiences")
    crud_instance = CRUDExperience(client=http_auth_client)

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
