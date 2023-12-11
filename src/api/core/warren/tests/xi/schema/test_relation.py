"""Tests for the Experience Index Schema Relation."""

from datetime import timezone
from uuid import UUID

import pytest
from freezegun import freeze_time
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from warren.xi.enums import RelationType
from warren.xi.factories import (
    ExperienceFactory,
    RelationFactory,
)
from warren.xi.schema import Experience, Relation


def test_relation_create(db_session: Session):
    """Test creating a relation with valid data."""
    RelationFactory.__session__ = db_session

    # Assert the database contains no relation
    relations = db_session.exec(select(Relation)).all()
    assert len(relations) == 0

    # Assert the database contains no experience
    experiences = db_session.exec(select(Experience)).all()
    assert len(experiences) == 0

    # Generate randomized valid relation data
    relation_data = RelationFactory.build().model_dump(
        exclude={"id", "created_at", "updated_at"}
    )

    # Assert the database contains two new experiences
    experiences = db_session.exec(select(Experience)).all()
    assert len(experiences) == 2

    # Attempt creating a first relation with valid data
    time = RelationFactory.__faker__.date_time(timezone.utc)
    with freeze_time(time):
        relation = RelationFactory.create_sync(**relation_data)

    # Assert the generated primary key is a valid UUID
    assert isinstance(relation.id, UUID)

    # Verify that the first relation has been correctly saved
    saved_relation = db_session.get(Relation, relation.id)
    assert saved_relation == Relation(
        id=relation.id,
        created_at=time,
        updated_at=time,
        **relation_data,
    )

    # Assert the database contains one relation
    relations = db_session.exec(select(Relation)).all()
    assert len(relations) == 1

    # Read the two experiences described in the relation
    experience_source = db_session.get(Experience, saved_relation.source_id)
    experience_target = db_session.get(Experience, saved_relation.target_id)

    # Assert source experience has only one relation
    assert experience_source.relations_source == [saved_relation]
    assert experience_source.relations_target == []

    # Assert target experience has only one relation
    assert experience_target.relations_source == []
    assert experience_target.relations_target == [saved_relation]


def test_relation_create_partially_duplicated(db_session: Session):
    """Test creating a relation partially duplicated."""
    RelationFactory.__session__ = db_session

    # Assert the database contains no relation
    relations = db_session.exec(select(Relation)).all()
    assert len(relations) == 0

    # Generate randomized valid relation data
    relation = RelationFactory.create_sync()

    # Assert the database contains one relation
    relations = db_session.exec(select(Relation)).all()
    assert len(relations) == 1

    available_kind_values = list(RelationType)
    available_kind_values.remove(relation.kind)

    # Attempt creating the relation in the database
    RelationFactory.create_sync(
        source_id=relation.source_id,
        target_id=relation.target_id,
        kind=ExperienceFactory.__random__.choice(available_kind_values),
    )

    # Assert the database contains one more relation
    relations = db_session.exec(select(Relation)).all()
    assert len(relations) == 2


def test_relation_create_duplicated(db_session: Session):
    """Test creating a relation duplicated."""
    RelationFactory.__session__ = db_session

    # Assert the database contains no relation
    relations = db_session.exec(select(Relation)).all()
    assert len(relations) == 0

    # Generate randomized valid relation data
    relation = RelationFactory.create_sync()

    # Assert the database contains one relation
    relations = db_session.exec(select(Relation)).all()
    assert len(relations) == 1

    # Attempt creating the relation in the database
    with pytest.raises(
        IntegrityError,
        match='violates unique constraint "relation_source_id_target_id_kind_key"',
    ):
        RelationFactory.create_sync(
            source_id=relation.source_id,
            target_id=relation.target_id,
            kind=relation.kind,
        )


def test_relation_create_bidirectional(db_session: Session):
    """Test creating a bidirectional relation."""
    RelationFactory.__session__ = db_session

    # Assert the database contains no relation
    relations = db_session.exec(select(Relation)).all()
    assert len(relations) == 0

    # Generate randomized valid relation data
    relation = RelationFactory.create_sync()

    # Assert the database contains one relation
    relations = db_session.exec(select(Relation)).all()
    assert len(relations) == 1

    # Attempt creating relation with inverted source and target in the database
    RelationFactory.create_sync(
        source_id=relation.target_id,
        target_id=relation.source_id,
        kind=relation.kind,
    )

    # Assert the database contains one more relation
    relations = db_session.exec(select(Relation)).all()
    assert len(relations) == 2


def test_relation_create_self_referential(db_session: Session):
    """Test creating a self-referential relation."""
    RelationFactory.__session__ = ExperienceFactory.__session__ = db_session

    # Assert the database contains no relation
    experience = db_session.exec(select(Experience)).all()
    assert len(experience) == 0

    # Create an experience in the database
    experience = ExperienceFactory.create_sync()

    # Assert the database contains one experience
    experiences = db_session.exec(select(Experience)).all()
    assert len(experiences) == 1

    # Attempt creating a self-referential relation in the database
    with pytest.raises(
        IntegrityError, match='violates check constraint "no-self-referential"'
    ):
        RelationFactory.create_sync(
            source_id=experience.id,
            target_id=experience.id,
        )


def test_relation_update(db_session: Session):
    """Test updating a relation."""
    RelationFactory.__session__ = ExperienceFactory.__session__ = db_session

    # Assert the database contains no relation
    relations = db_session.exec(select(Relation)).all()
    assert len(relations) == 0

    # Assert the database contains no experience
    experiences = db_session.exec(select(Experience)).all()
    assert len(experiences) == 0

    # Get two random dates for creating and updating a relation
    creation_date = ExperienceFactory.__faker__.date_time(timezone.utc)
    update_date = ExperienceFactory.__faker__.date_time_between(
        creation_date, tzinfo=timezone.utc
    )

    # Create a relation in the database
    with freeze_time(creation_date):
        relation = RelationFactory.create_sync()

    # Assert the database contains two new experiences
    experiences = db_session.exec(select(Experience)).all()
    assert len(experiences) == 2

    # Assert the initial 'updated_at' field is equal to the creation date
    assert relation.created_at == creation_date
    assert relation.updated_at == creation_date

    # Create a third experience to update the relation's source
    source_id_removed = relation.source_id
    third_experience = ExperienceFactory.create_sync()

    # Assert the database contains one more experiences
    experiences = db_session.exec(select(Experience)).all()
    assert len(experiences) == 3

    # Attempt updating the relation's source with the third experience
    with freeze_time(update_date):
        relation.source_id = third_experience.id
        db_session.add(relation)
        db_session.commit()

    # Assert the initial 'updated_at' field has been updated
    assert relation.created_at == creation_date
    assert relation.updated_at == update_date

    # Assert that the 'source_id' attribute has been updated
    assert relation.source_id == third_experience.id

    # Assert the update has not created any new relation
    relations = db_session.exec(select(Relation)).all()
    assert len(relations) == 1

    # Read the three experiences
    experience_source = db_session.get(Experience, relation.source_id)
    experience_target = db_session.get(Experience, relation.target_id)
    experience_source_removed = db_session.get(Experience, source_id_removed)

    # Assert source experience has only one relation
    assert experience_source.relations_source == [relation]
    assert experience_source.relations_target == []

    # Assert source experience has only one relation
    assert experience_target.relations_source == []
    assert experience_target.relations_target == [relation]

    # Assert the initial source experience has no more relation
    assert experience_source_removed.relations_source == []
    assert experience_source_removed.relations_target == []
