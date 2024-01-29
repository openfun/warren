"""Experience Index SQL Models."""

from datetime import datetime, timezone
from typing import List, Optional, Tuple, Union
from uuid import UUID, uuid4

from pydantic import Json, PositiveInt
from sqlalchemy import CheckConstraint, Column, Constraint, UniqueConstraint
from sqlalchemy import Enum as SAEnum
from sqlalchemy.types import JSON, DateTime
from sqlmodel import Field, Relationship, SQLModel

from warren.fields import IRI

from .enums import AggregationLevel, RelationType, Structure


class BaseTimestamp(SQLModel):  # type: ignore[misc]
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
        default_factory=lambda: datetime.now(timezone.utc),
        description="The timestamp indicating when the record was created.",
    )
    updated_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc)
        ),
        default_factory=lambda: datetime.now(timezone.utc),
        description="The timestamp indicating when the record was last updated.",
    )


class Relation(BaseTimestamp, table=True):  # type: ignore[call-arg, misc]
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


JsonField = Union[List[dict[str, str]], dict[str, str], List[str], Json]


class Experience(BaseTimestamp, table=True):  # type: ignore[call-arg, misc]
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
        CheckConstraint("duration > 0", name="positive-duration"),
    )
    id: Optional[UUID] = Field(default_factory=lambda: uuid4().hex, primary_key=True)
    iri: IRI = Field(
        description="A globally unique label that identifies this learning object",
    )
    title: JsonField = Field(
        sa_column=Column(JSON), description="Name given to this learning object."
    )
    language: str = Field(
        max_length=100,
        description=(
            "The primary human language or languages used within this learning"
            " object to communicate to the intended user."
        ),
    )
    description: JsonField = Field(
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
    technical_datatypes: JsonField = Field(
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
