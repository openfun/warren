"""Test indicators models."""
import json
from datetime import datetime, timezone
from uuid import UUID

import pytest
from pydantic import ValidationError
from sqlmodel import select

from warren.indicators.models import CacheEntry, CacheEntryCreate


@pytest.mark.parametrize("value", [{"foo": [1, 2, 3]}, '{"foo": [1, 2, 3]}', [1, 2, 3]])
def test_cache_model_with_supported_value_types(value, db_session):
    """Test the CacheEntry model given a dict, list or JSON string 'value'."""
    cache = CacheEntryCreate(key="my-super-key", value=value)
    assert cache.key == "my-super-key"
    assert cache.value == value or json.loads(value)
    assert cache.id is not None
    # Validate the identifier as a valid UUID hex string representation
    assert UUID(cache.id)
    assert cache.since is None
    assert cache.until is None
    assert cache.created_at is not None
    assert isinstance(cache.created_at, datetime)
    assert cache.created_at.tzinfo is not None

    db_session.add(CacheEntry.from_orm(cache))
    db_session.commit()

    saved = db_session.exec(select(CacheEntry).where(CacheEntry.key == cache.key)).one()
    assert saved.id == UUID(cache.id)
    assert saved.key == cache.key
    assert saved.value == cache.value
    assert saved.since is None
    assert saved.until is None
    assert saved.created_at == cache.created_at
    assert saved.created_at.tzinfo is not None


@pytest.mark.parametrize("value", ["not_json", 1, True])
def test_cache_model_with_unsupported_value_types(value, db_session):
    """Test the CacheEntry model with unsupported value types."""
    with pytest.raises(ValidationError):
        CacheEntryCreate(key="my-super-key", value=value)


def test_cache_model_since_until_tz_awareness(db_session):
    """Test the timezone awareness of since and until fields."""
    # By default, the creation model does not make datetime fields timezone aware
    cache = CacheEntryCreate(
        key="my-super-key",
        value=[1, 2, 3],
        since=datetime(2023, 1, 1),
        until=datetime(2023, 1, 31),
    )
    assert cache.since.tzinfo is None
    assert cache.until.tzinfo is None

    db_session.add(CacheEntry.from_orm(cache))
    db_session.commit()

    saved = db_session.exec(select(CacheEntry).where(CacheEntry.key == cache.key)).one()
    # Once saved, datetime fields should be timezone aware and defaults to UTC
    assert saved.since.tzinfo is not None
    assert saved.since.tzinfo == timezone.utc
    assert saved.until.tzinfo is not None
    assert saved.until.tzinfo == timezone.utc
