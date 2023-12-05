"""Tests for the Experience Index Schema Experience."""

from datetime import timedelta, timezone
from uuid import UUID, uuid4

import pytest
from freezegun import freeze_time
from sqlalchemy.exc import DataError, IntegrityError
from sqlmodel import Session, select

from warren.xi.enums import AggregationLevel, Structure
from warren.xi.factories import (
    ExperienceFactory,
    RelationFactory,
)
from warren.xi.schema import Experience


def test_experience_create(db_session: Session):
    """Test creating an experience with valid data."""
    ExperienceFactory.__session__ = db_session

    # Assert the database is empty
    experiences = db_session.exec(select(Experience)).all()
    assert len(experiences) == 0

    # Generate randomized valid experience data
    experience_data = ExperienceFactory.build_dict()

    # Attempt creating a first experience with valid data
    time = ExperienceFactory.__faker__.date_time(timezone.utc)
    with freeze_time(time):
        experience = Experience(**experience_data)
        db_session.add(experience)
        db_session.commit()

    # Assert the generated primary key is a valid UUID
    assert isinstance(experience.id, UUID)

    # Verify that the first experience has been correctly saved
    assert db_session.get(Experience, experience.id) == Experience(
        id=experience.id,
        created_at=time,
        updated_at=time,
        relations_source=[],
        relations_target=[],
        **experience_data,
    )

    # Assert the database contains one experience
    experiences = db_session.exec(select(Experience)).all()
    assert len(experiences) == 1


def test_experience_create_invalid_timestamps(db_session: Session):
    """Test creating an experience with invalid timestamps."""
    ExperienceFactory.__session__ = db_session

    # Assert the database is empty
    experiences = db_session.exec(select(Experience)).all()
    assert len(experiences) == 0

    # Generate an 'update_date'
    update_date = ExperienceFactory.__faker__.date_time(timezone.utc)

    # Generate a 'creation_date' posterior to the 'update_date'
    creation_date = ExperienceFactory.__faker__.date_time_between(
        update_date, tzinfo=timezone.utc
    )

    # Attempt creating an invalid experience in the database
    with pytest.raises(
        IntegrityError,
        match='"experience" violates check constraint "pre-creation-update"',
    ):
        ExperienceFactory.create_sync(created_at=creation_date, updated_at=update_date)


def test_experience_create_non_utc_timestamps(db_session: Session):
    """Test creating an experience with non-utc timestamps."""
    ExperienceFactory.__session__ = db_session

    # Create an experience object with given random timestamps
    timestamp_non_utc = ExperienceFactory.__faker__.date_time(
        timezone(timedelta(hours=4))
    )

    # Attempt creating the experience in the database
    experience = ExperienceFactory.create_sync(
        created_at=timestamp_non_utc, updated_at=timestamp_non_utc
    )

    # Verify that the experience has been correctly saved
    saved_experience = db_session.get(Experience, experience.id)

    # Assert the timestamp were correctly saved
    assert saved_experience.created_at == timestamp_non_utc
    assert saved_experience.updated_at == timestamp_non_utc

    # Assert the database contains one experience
    experiences = db_session.exec(select(Experience)).all()
    assert len(experiences) == 1


def test_experience_create_duplicated_iri(db_session: Session):
    """Test creating an experience with a duplicated IRI."""
    ExperienceFactory.__session__ = db_session
    duplicated_iri = f"uuid://{uuid4().hex}"

    # Create an experience in the database with a specific IRI
    ExperienceFactory.create_sync(iri=duplicated_iri)

    # Assert the database contains one experience
    experiences = db_session.exec(select(Experience)).all()
    assert len(experiences) == 1

    # Attempt creating another experience with the same IRI
    with pytest.raises(
        IntegrityError,
        match='duplicate key value violates unique constraint "experience_iri_key"',
    ):
        ExperienceFactory.create_sync(iri=duplicated_iri)


@pytest.mark.parametrize(
    "invalid_duration",
    [-100, -1, -2000, 0],
)
def test_experience_create_negative_duration(
    db_session: Session, invalid_duration: int
):
    """Test creating an experience with an invalid duration."""
    # Create an experience object with valid data
    experience = ExperienceFactory.build()

    # Assert the database is empty
    experiences = db_session.exec(select(Experience)).all()
    assert len(experiences) == 0

    # Update it with an invalid 'duration'
    experience.duration = invalid_duration

    # Attempt creating an invalid experience in the database
    with pytest.raises(
        IntegrityError,
        match='"experience" violates check constraint "positive-duration"',
    ):
        db_session.add(experience)
        db_session.commit()


def test_experience_create_with_read_only(db_session: Session):
    """Test creating an experience with read-only attributes."""
    RelationFactory.__session__ = db_session

    # Create an experience object
    experience = ExperienceFactory.build()

    # Assert the database is empty
    experiences = db_session.exec(select(Experience)).all()
    assert len(experiences) == 0

    # Create a relation object
    relation = RelationFactory.build()

    # Assert the database contains the two experiences from the relation
    experiences = db_session.exec(select(Experience)).all()
    assert len(experiences) == 2

    # Set experience read-only attributes with the relation
    experience.relations_source = [relation]
    experience.relations_target = [relation]

    # Create the experience in the database
    # No error should be triggered, read-only attributes are ignored
    db_session.add(experience)
    db_session.commit()

    # Get the saved experience
    saved_experience = db_session.get(Experience, experience.id)

    # Assert the database contains the right number of experiences
    experiences = db_session.exec(select(Experience)).all()
    assert len(experiences) == 3

    # Assert experiences read-only attributes were not set
    assert saved_experience.relations_source == []
    assert saved_experience.relations_target == []


@pytest.mark.parametrize(
    "language_length",
    [201, 500, 1020],
)
def test_experience_create_with_too_long_language(
    db_session: Session, language_length: int
):
    """Test creating an experience with a too long language."""
    # Create an experience object with valid data
    experience = ExperienceFactory.build()

    # Assert the database is empty
    experiences = db_session.exec(select(Experience)).all()
    assert len(experiences) == 0

    # Update it with an invalid 'language'
    experience.language = ExperienceFactory.__faker__.pystr(
        min_chars=language_length, max_chars=language_length
    )

    # Attempt creating an invalid experience in the database
    with pytest.raises(DataError, match="value too long for type character"):
        db_session.add(experience)
        db_session.commit()


@pytest.mark.anyio
async def test_experience_read_with_relation(db_session: Session):
    """Test retrieving experiences with a relation."""
    ExperienceFactory.__session__ = RelationFactory.__session__ = db_session

    # Create some experiences in the database
    number_experiences = 10
    ExperienceFactory.create_batch_sync(number_experiences)

    # Assert the database contains the right number of experiences
    experiences = db_session.exec(select(Experience)).all()
    assert len(experiences) == number_experiences

    # Create a relation in the database
    relation = RelationFactory.create_sync()

    # Assert the database contains two new experiences,
    # created when creating the relation
    experiences = db_session.exec(select(Experience)).all()
    assert len(experiences) == number_experiences + 2

    db_session.refresh(relation)

    # Read the two experiences described in the relation
    experience_source = db_session.get(Experience, relation.source_id)
    experience_target = db_session.get(Experience, relation.target_id)

    # Assert source experience has one relation
    assert experience_source.relations_source == [relation]
    assert experience_source.relations_target == []

    # Assert target experience has one relation
    assert experience_target.relations_source == []
    assert experience_target.relations_target == [relation]

    # Delete the relation from the database
    db_session.delete(relation)
    db_session.commit()

    # Assert source experience has no relation
    assert experience_source.relations_source == []
    assert experience_source.relations_target == []

    # Assert target experience has no relation
    assert experience_target.relations_source == []
    assert experience_target.relations_target == []


@pytest.mark.parametrize(
    "update_data",
    [
        {"iri": f"uuid://{uuid4().hex}"},
        {
            "title": {"en": ExperienceFactory.__faker__.sentence(nb_words=5)},
            "duration": ExperienceFactory.__faker__.pyint(),
        },
        {"description": {"en": ExperienceFactory.__faker__.paragraph(nb_sentences=1)}},
        {
            "structure": ExperienceFactory.__random__.choice(list(Structure)),
            "iri": f"uuid://{uuid4().hex}",
        },
        {
            "aggregation_level": ExperienceFactory.__random__.choice(
                list(AggregationLevel)
            ),
            "iri": f"uuid://{uuid4().hex}",
        },
    ],
)
def test_experience_update(db_session: Session, update_data: dict):
    """Test updating an experience with various update scenarios."""
    ExperienceFactory.__session__ = db_session

    # Get two random dates for creating and updating an experience
    creation_date = ExperienceFactory.__faker__.date_time(timezone.utc)
    update_date = ExperienceFactory.__faker__.date_time_between(
        creation_date, tzinfo=timezone.utc
    )

    # Create an experience in the database
    with freeze_time(creation_date):
        experience = ExperienceFactory.create_sync()

    # Assert the initial 'updated_at' field is equal to the creation date
    assert experience.updated_at == creation_date

    # Update the experience with some valid data
    with freeze_time(update_date):
        for key, value in update_data.items():
            setattr(experience, key, value)
        db_session.add(experience)
        db_session.commit()

    # Check if specified fields in the experience match the expected values
    for key, value in update_data.items():
        assert getattr(experience, key) == value

    # Check untouched fields in the experience match the initial values
    for key, value in experience.dict(
        exclude={"created_at", "updated_at", *update_data.keys()}
    ).items():
        assert getattr(experience, key) == value

    # Assert that the 'updated_at' attribute has been updated
    assert experience.updated_at == update_date

    # Assert that the 'created_at' attribute has not been updated
    assert experience.created_at == creation_date

    # Assert the update has not created any new experience
    experiences = db_session.exec(select(Experience)).all()
    assert len(experiences) == 1


@pytest.mark.parametrize(
    "attribute_name",
    ["structure", "aggregation_level"],
)
def test_experience_update_invalid_enum(db_session: Session, attribute_name):
    """Test updating an experience with invalid enum data."""
    ExperienceFactory.__session__ = db_session

    # Create an experience in the database
    experience = ExperienceFactory.create_sync()

    # Assert the database contains one experience
    experiences = db_session.exec(select(Experience)).all()
    assert len(experiences) == 1

    # Update experience's attribute with an invalid value
    setattr(experience, attribute_name, "foo.")

    # Attempt updating the experience with invalid data
    with pytest.raises(DataError) as exc_info:
        db_session.add(experience)
        db_session.commit()

    # Experience's update should fail due to invalid enum data
    attribute_name = attribute_name.replace("_", "")
    assert f'invalid input value for enum {attribute_name}: "foo."' in str(
        exc_info.value
    )


def test_experience_delete_with_relation_still_attached(db_session: Session):
    """Test deleting an experience attached to a relation."""
    RelationFactory.__session__ = db_session

    # Assert the database is empty
    experiences = db_session.exec(select(Experience)).all()
    assert len(experiences) == 0

    relation = RelationFactory.create_sync()

    # Assert the database contains two experiences, one source and one target
    experiences = db_session.exec(select(Experience)).all()
    assert len(experiences) == 2

    # Get the source experience attached to the relation
    experience_source = db_session.get(Experience, relation.source_id)

    with pytest.raises(
        IntegrityError,
        match='violates foreign key constraint "relation_source_id_fkey"',
    ):
        db_session.delete(experience_source)
        db_session.commit()
