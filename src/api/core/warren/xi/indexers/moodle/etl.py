"""Moodle Experience Index indexers."""

import logging
import re
from itertools import chain
from typing import Iterator, List, Union
from uuid import UUID

from httpx import HTTPError
from pydantic import ValidationError

from warren.fields import IRI

from ...client import ExperienceIndex
from ...enums import RelationType
from ...models import (
    ExperienceCreate,
    ExperienceRead,
)
from ...schema import Experience
from ..etl import ETL, ETLRunnerMixin
from .client import LMS
from .models import Course, Section

logger = logging.getLogger(__name__)


class Courses(ETL[Course, ExperienceCreate], ETLRunnerMixin):
    """Index Moodle courses.

    This class extracts courses from Moodle, transforms them into experiences,
    and loads them into the Experience Index (XI).
    """

    def __init__(
        self, lms: LMS, xi: ExperienceIndex, ignore_errors: bool = True, **kwargs
    ):
        """Initialize indexer with LMS and XI clients."""
        self._lms = lms
        self._xi = xi
        self._ignore_errors = ignore_errors

    @classmethod
    async def factory(cls, source: LMS, target: ExperienceIndex, **kwargs):
        """Instantiate the class."""
        return cls(lms=source, xi=target, **kwargs)

    async def _extract(self) -> List[Course]:
        """Extract all available courses from the LMS."""
        return await self._lms.get_courses()

    def _transform(self, raw: List[Course]) -> Iterator[ExperienceCreate]:
        """Transform courses into experiences."""
        return (course.to_experience(base_url=self._lms.url) for course in raw)

    async def _load(self, data: Iterator[ExperienceCreate]) -> None:
        """Load experiences into the Experience Index (XI)."""
        for experience in data:
            try:
                await self._xi.experience.create_or_update(experience)
            except HTTPError as err:
                if not self._ignore_errors:
                    raise err
                logger.exception(
                    "Error occurred, skipping experience %s", experience.iri
                )


class CourseContent(ETL[Section, ExperienceCreate], ETLRunnerMixin):
    """Index Moodle modules for a given course.

    This class extracts modules from Moodle, transforms them into experiences,
    and loads them into the Experience Index (XI).
    """

    def __init__(
        self,
        lms: LMS,
        xi: ExperienceIndex,
        course: ExperienceRead,
        ignore_errors: bool = True,
        **kwargs,
    ):
        """Initialize indexer with clients (LMS, XI) and the course."""
        self._lms = lms
        self._xi = xi
        self._course = course
        self._ignore_errors = ignore_errors

    @classmethod
    async def factory(
        cls, source: LMS, target: ExperienceIndex, course_iri: IRI, **kwargs
    ):
        """Instantiate the class after fetching the given course."""
        course = await target.experience.get(course_iri)
        if not course:
            raise ValueError(f"Wrong course IRI {course_iri}")

        return cls(lms=source, xi=target, course=course, **kwargs)

    @property
    def _course_id(self) -> int:
        """Extract the course ID from the course's IRI."""
        match = re.search(r"id=(\d+)", self._course.iri)
        if match is None:
            raise ValueError("Course ID not found in the course's IRI")
        return int(match.group(1))

    async def _extract(self) -> List[Section]:
        """Extract course contents (sections/modules) from the LMS."""
        return await self._lms.get_course_contents(course_id=self._course_id)

    def _transform(self, raw: List[Section]) -> Iterator[ExperienceCreate]:
        """Transform modules into experiences."""
        # Extract modules from section
        modules = chain(*[section.modules for section in raw])

        # Convert all modules to experience using language from the course
        for module in modules:
            try:
                yield module.to_experience(self._course.language)
            except ValidationError as err:
                if not self._ignore_errors:
                    raise err
                logger.exception("Skipping invalid module %s", module.id)

    async def _load(self, data: Iterator[ExperienceCreate]) -> None:
        """Load experiences into the Experience Index (XI) and create relations."""
        for experience in data:
            try:
                # If a new experience is created, it will return a UUID
                response: Union[UUID, Experience] = (
                    await self._xi.experience.create_or_update(experience)
                )

                # If it's a new experience, create relations to its course
                if isinstance(response, UUID):
                    await self._xi.relation.create_bidirectional(
                        self._course.id,
                        response,
                        (RelationType.ISPARTOF, RelationType.HASPART),
                    )

            except HTTPError as err:
                if not self._ignore_errors:
                    raise err
                logger.exception(
                    "Error occurred, skipping experience %s", experience.iri
                )
