"""Moodle indexers' models."""

from typing import List, Optional
from enum import Enum
from pydantic import Field
from pydantic.main import BaseModel

from warren.conf import settings
from warren.fields import IRI

from ...enums import AggregationLevel, Structure
from ...models import (
    ExperienceCreate,
)
from ..mixins import LangStringMixin


class Activities(Enum):
    ASSIGNMENT = "mod_assign"
    LIVE_SESSION = "mod_bigbluebuttonbn"
    BOOK = "mod_book"
    CHAT = "mod_chat"
    CHOICE = "mod_choice"
    DATA = "mod_data"
    MEETING = "mod_facetoface"
    FEEDBACK = "mod_feedback"
    FOLDER = "mod_folder"
    FORUM = "mod_forum"
    GLOSSARY = "mod_glossary"
    IMCSP = "mod_imcsp"
    LESSON = "mod_lesson"
    LTI = "mod_lti"
    PAGE = "mod_page"
    QUIZ = "mod_quiz"
    RESOURCE = "mod_resource"
    SCORM = "mod_scorm"
    SURVEY = "mod_survey"
    URL = "mod_url"
    WIKI = "mod_wiki"
    WORKSHOP = "mod_workshop"
    PROGRAM = "totara_program"


class Module(BaseModel, LangStringMixin):
    """Model for a Moodle module."""

    id: int
    url: Optional[IRI]
    name: str
    modname: Activities
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
            title=self.build_lang_string(self.display_name, settings.XI_DEFAULT_LANG),
            language=self.language or settings.XI_DEFAULT_LANG,
            description=self.build_lang_string(self.summary, settings.XI_DEFAULT_LANG),
            structure=Structure.HIERARCHICAL,
            aggregation_level=AggregationLevel.THREE,
            technical_datatypes=[],
        )
