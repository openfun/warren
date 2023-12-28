"""Moodle indexers' models."""

from typing import List, Optional

from pydantic import Field
from pydantic.main import BaseModel

from warren.fields import IRI

from ...enums import AggregationLevel, Structure
from ...models import (
    ExperienceCreate,
)
from ..mixins import LangStringMixin


class Module(BaseModel, LangStringMixin):
    """Model for a Moodle module."""

    id: int
    url: Optional[IRI]
    name: str
    modname: str  # todo - should it be an enum
    description: Optional[str]

    def to_experience(self, language: str) -> ExperienceCreate:
        """Convert module to an experience."""
        return ExperienceCreate(
            iri=self.url,
            title=self.build_lang_string(self.name, language),
            language=language,
            description=self.build_lang_string(self.description, language),
            structure=Structure.ATOMIC,
            aggregation_level=AggregationLevel.ONE,
            technical_datatypes=[
                self.modname
            ],  # todo - not appropriate, create a new field?
        )


class Section(BaseModel):
    """Model for a Moodle section."""

    id: int
    name: str
    modules: List[Module]


class Course(BaseModel, LangStringMixin):
    """Model for a Moodle course."""

    id: int
    language: str = Field(alias="lang")
    display_name: str = Field(alias="displayname")
    summary: str
    time_created: int = Field(alias="timecreated")
    time_modified: int = Field(alias="timemodified")

    def to_experience(self, base_url) -> ExperienceCreate:
        """Convert course to an experience."""
        return ExperienceCreate(
            iri=f"{base_url}/course/view.php?id={self.id}",
            title=self.build_lang_string(self.display_name),
            language=self.language,
            description=self.build_lang_string(self.summary),
            structure=Structure.HIERARCHICAL,
            aggregation_level=AggregationLevel.THREE,
            technical_datatypes=[],
        )
