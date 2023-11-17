"""Experience Index SQL and Pydantic Models."""
from datetime import datetime
from enum import Enum, IntEnum, unique
from typing import List, Optional, Tuple, Union
from uuid import UUID, uuid4

from pydantic import Json, PositiveInt
from pydantic.main import BaseModel
from sqlalchemy import CheckConstraint, Column, Constraint, UniqueConstraint
from sqlalchemy import Enum as SAEnum
from sqlalchemy.types import JSON, DateTime
from sqlmodel import Field, Relationship, SQLModel

from warren.fields import IRI


class BaseTimestamp(SQLModel):
    """A base class for SQL models with timestamp fields.

    This class provides two timestamp fields, `created_at` and `updated_at`, which are
    automatically managed. The `created_at` field is set to the current UTC time when
    a new record is created, and the `updated_at` field is updated to the current UTC
    time whenever the record is modified.
    """

    __table_args__: Tuple[Constraint, ...] = (
        CheckConstraint("created_at <= updated_at", name="pre-creation-update"),
    )
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True)),
        default_factory=lambda: datetime.utcnow(),
        description="The timestamp indicating when the record was created.",
    )
    updated_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), onupdate=lambda: datetime.utcnow()),
        default_factory=lambda: datetime.utcnow(),
        description="The timestamp indicating when the record was last updated.",
    )


class TimestampRead(BaseModel):
    """Model for reading timestamp values."""

    created_at: datetime
    updated_at: datetime


@unique
class RelationType(str, Enum):
    """Nature of the relationship between two LOM (experiences)."""

    ISPARTOF = "ispartof"
    HASPART = "haspart"
    ISVERSIONOF = "isversionof"
    HASVERSION = "hasversion"
    ISFORMATOF = "isformatof"
    HASFORMAT = "hasformat"
    REFERENCES = "references"
    ISREFERENCEDBY = "isreferencedby"
    ISBASEDON = "isbasedon"
    ISBASISFOR = "isbasisfor"
    REQUIRES = "requires"
    ISREQUIREDBY = "isrequiredby"


class Relation(BaseTimestamp, table=True):
    """Association table for relationships between two LOM (experiences)."""

    __table_args__ = (
        *BaseTimestamp.__table_args__,
        UniqueConstraint("source_id", "target_id", "kind"),
        CheckConstraint("source_id != target_id", name="no-self-referential"),
    )
    id: Optional[UUID] = Field(default_factory=lambda: uuid4().hex, primary_key=True)
    source_id: UUID = Field(
        foreign_key="experience.id",
        description="The source learning object that this relationship references.",
    )
    target_id: UUID = Field(
        foreign_key="experience.id",
        description="The target learning object that this relationship references.",
    )
    kind: RelationType = Field(
        sa_column=Column(SAEnum(RelationType)),
        description=(
            "Nature of the relationship between the source learning object "
            "and the target learning object."
        ),
    )


@unique
class Structure(str, Enum):
    """Enumeration of Experience Structures."""

    ATOMIC = "atomic"
    COLLECTION = "collection"
    NETWORKED = "networked"
    HIERARCHICAL = "hierarchical"
    LINEAR = "linear"


@unique
class AggregationLevel(IntEnum):
    """Enumeration of Experience Aggregation Levels."""

    ONE = 1
    TWO = 2
    THREE = 3
    FOUR = 4


class Experience(BaseTimestamp, table=True):
    """Model representing a learning object (LOM or experience).

    Most JSON fields are designed to store translatable text. Each key represents
    a language, and its corresponding value is the text in that language. This
    aligns with the LangString model defined in IEEE Std 1484.12.1-2020.

    Example:
        description = "{'en': 'Description of the LOM'}"
    """

    __table_args__ = (
        *BaseTimestamp.__table_args__,
        UniqueConstraint("iri"),
        CheckConstraint("duration >= 0", name="positive-duration"),
    )
    id: Optional[UUID] = Field(default_factory=lambda: uuid4().hex, primary_key=True)
    iri: IRI = Field(
        description="A globally unique label that identifies this learning object",
    )
    title: Json = Field(
        sa_column=Column(JSON), description="Name given to this learning object."
    )
    language: str = Field(
        max_length=100,
        description=(
            "The primary human language or languages used within this learning"
            " object to communicate to the intended user."
        ),
    )
    description: Json = Field(
        sa_column=Column(JSON),
        description="A textual description of the content of this learning object.",
    )
    structure: Structure = Field(
        sa_column=Column(SAEnum(Structure)),
        description="Underlying organizational structure of this learning object.",
    )
    aggregation_level: AggregationLevel = Field(
        sa_column=Column(SAEnum(AggregationLevel)),
        description="The functional granularity of this learning object.",
    )
    technical_datatypes: Json = Field(
        sa_column=Column(JSON),
        description=(
            "The technical requirements and characteristics of this learning object."
        ),
    )
    duration: Optional[PositiveInt] = Field(
        description=(
            "Time a continuous learning object takes when played at intended speed."
        )
    )
    relations_source: Optional[List[Relation]] = Relationship(
        link_model=Relation,
        sa_relationship_kwargs={
            "lazy": "immediate",
            "primaryjoin": "Experience.id==Relation.source_id",
            "secondaryjoin": "Experience.id==Relation.target_id",
            "viewonly": True,
        },
    )
    relations_target: Optional[List[Relation]] = Relationship(
        link_model=Relation,
        sa_relationship_kwargs={
            "lazy": "immediate",
            "primaryjoin": "Experience.id==Relation.target_id",
            "secondaryjoin": "Experience.id==Relation.source_id",
            "viewonly": True,
        },
    )


JsonField = Union[List[dict], dict, List[str]]


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
