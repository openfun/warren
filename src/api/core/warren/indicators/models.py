"""Indicators SQL Models."""
from datetime import datetime, timezone
from typing import Optional, Union
from uuid import UUID, uuid4

from pydantic import Json
from sqlalchemy import Column
from sqlalchemy.types import JSON as SAJson
from sqlalchemy.types import DateTime
from sqlmodel import Field, SQLModel


class CacheEntryCreate(SQLModel):
    """Indicator generic persistency."""

    id: Optional[UUID] = Field(default_factory=lambda: uuid4().hex, primary_key=True)
    key: str = Field(max_length=100, index=True)
    value: Union[dict, list, Json] = Field(sa_column=Column(SAJson))
    since: Optional[datetime] = Field(sa_column=Column(DateTime(timezone=True)))
    until: Optional[datetime] = Field(sa_column=Column(DateTime(timezone=True)))
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True)),
        default_factory=lambda: datetime.now(timezone.utc),
    )


class CacheEntry(CacheEntryCreate, table=True):
    """Indicator generic persistency (table version)."""
