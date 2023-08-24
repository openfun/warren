"""Indicators SQL Models."""

from typing import Optional
from uuid import UUID, uuid4

from pydantic import Json
from sqlalchemy import Column
from sqlalchemy.types import JSON as SAJson
from sqlmodel import Field, SQLModel


class Cache(SQLModel, table=True):
    """Indicator generic persistency."""

    id: Optional[UUID] = Field(default=uuid4, primary_key=True)
    key: str = Field(max_length=100, index=True)
    value: Json = Field(sa_column=Column(SAJson))
