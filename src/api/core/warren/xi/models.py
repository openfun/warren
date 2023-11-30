"""Experience Index Pydantic Models."""
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import Json, PositiveInt
from pydantic.main import BaseModel

from warren.fields import IRI

from .enums import AggregationLevel, RelationType, Structure
from .schema import JsonField


class TimestampRead(BaseModel):
    """Model for reading timestamp values."""

    created_at: datetime
    updated_at: datetime


class RelationCreate(BaseModel):
    """Model for creating a relation."""

    source_id: UUID
    target_id: UUID
    kind: RelationType


class RelationUpdate(BaseModel):
    """Model for updating a relation."""

    source_id: Optional[UUID]
    target_id: Optional[UUID]
    kind: Optional[RelationType]


class RelationRead(TimestampRead):
    """Model for reading information about a relation."""

    id: UUID
    source_id: UUID
    target_id: UUID
    kind: RelationType


class ExperienceCreate(BaseModel):
    """Model for creating an experience."""

    iri: IRI
    title: Json
    language: str
    description: Json
    structure: Structure
    aggregation_level: AggregationLevel
    technical_datatypes: Json
    duration: Optional[PositiveInt]


class ExperienceReadSnapshot(BaseModel):
    """Model for reading snapshot information about an experience."""

    id: UUID
    title: JsonField


class ExperienceUpdate(BaseModel):
    """Model for updating an experience."""

    iri: Optional[IRI]
    title: Optional[JsonField]
    language: Optional[str]
    description: Optional[JsonField]
    structure: Optional[Structure]
    aggregation_level: Optional[AggregationLevel]
    technical_datatypes: Optional[JsonField]
    duration: Optional[PositiveInt]


class ExperienceRead(ExperienceReadSnapshot, TimestampRead):
    """Model for reading detailed information about an experience."""

    class Config:
        """ExperienceRead model configuration."""

        orm_mode = True

    iri: IRI
    language: str
    description: JsonField
    structure: Structure
    aggregation_level: AggregationLevel
    technical_datatypes: JsonField
    duration: Optional[PositiveInt]
    relations_source: Optional[List[RelationRead]]
    relations_target: Optional[List[RelationRead]]
