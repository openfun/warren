"""Tests for Moodle Pydantic models."""

from uuid import uuid4

import pytest
from pydantic import ValidationError

from warren.xi.enums import AggregationLevel, Structure
from warren.xi.indexers.moodle.models import Course, Module
from warren.xi.models import ExperienceCreate


def test_module_to_experience():
    """Test converting a Module to an Experience."""
    module = Module(
        id=30,
        url=None,
        name="Lorem Ipsum",
        modname="forum",
        description="",
    )

    # Attempt converting the module without an IRI
    with pytest.raises(ValidationError):
        module.to_experience(language="fr")

    # Pass an IRI to the module
    iri = f"uuid://{uuid4().hex}"
    module.url = iri

    # Attempt converting the module to an Experience
    assert module.to_experience(language="fr") == ExperienceCreate(
        iri=iri,
        title={"fr": "Lorem Ipsum"},
        language="fr",
        description={"fr": ""},
        structure=Structure.ATOMIC,
        aggregation_level=AggregationLevel.ONE,
        technical_datatypes=["forum"],
    )


def test_course_to_experience():
    """Test converting a Course to an Experience."""
    course = Course(
        id=30,
        lang="fr",
        displayname="Lorem Ipsum",
        summary="",
        timecreated=1703147509,
        timemodified=1703153561,
    )

    assert course.to_experience(base_url="https://foo") == ExperienceCreate(
        iri="https://foo/course/view.php?id=30",
        title={"fr": "Lorem Ipsum"},
        language="fr",
        description={"fr": ""},
        structure=Structure.HIERARCHICAL,
        aggregation_level=AggregationLevel.THREE,
        technical_datatypes=[],
    )
