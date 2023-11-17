"""Experience Index Experiences and Relations Factories."""

import json
from typing import Any, Dict, Generic, List, Type, TypeVar
from uuid import uuid4

from polyfactory import Ignore, SyncPersistenceProtocol, Use
from polyfactory.factories.pydantic_factory import ModelFactory
from pydantic import BaseModel
from sqlmodel import Session

from warren.fields import IRI
from warren.xi.models import (
    Experience,
    Relation,
)

T = TypeVar("T", bound=BaseModel)


class SyncPersistenceHandler(Generic[T], SyncPersistenceProtocol[T]):
    """Sync persistence handler for SQLModelFactory."""

    def __init__(self, session: Session) -> None:
        """Initialize SyncPersistenceHandler with a SQLAlchemy Session.

        Args:
            session (Session): The SQLAlchemy session to be used for db operations.
        """
        self.session = session

    def save(self, data: T) -> T:
        """Save a single instance of data to the database.

        Args:
            data (T): The data instance to be saved.

        Raises:
            AttributeError: If the session is not set.

        Returns:
            T: The saved data instance.
        """
        if self.session is None:
            raise AttributeError("Session is not set")

        self.session.add(data)
        self.session.commit()
        return data

    def save_many(self, data: List[T]) -> List[T]:
        """Save multiple instances of data to the database.

        Args:
            data (List[T]): The list of data instances to be saved.

        Raises:
            AttributeError: If the session is not set.

        Returns:
            List[T]: The list of saved data instances.
        """
        if self.session is None:
            raise AttributeError("Session is not set")
        for d in data:
            self.session.add(d)
        self.session.commit()
        return data


class SQLModelFactory(Generic[T], ModelFactory[T]):
    """Base factory for SQLModel models."""

    __session__: Session
    __is_base_factory__ = True

    @classmethod
    def _get_sync_persistence(cls) -> SyncPersistenceProtocol[T]:
        """Initialize the SyncPersistenceHandler with the session."""
        return SyncPersistenceHandler[T](cls.__session__)


class IgnoreAutogeneratedFieldsMixin:
    """Mixin class to ignore autogenerated fields by SQLAlchemy.

    This class can be used as a mixin to exclude specific fields
    (such as id, created_at, updated_at) from being generated by factory.
    """

    id = Ignore()
    created_at = Ignore()
    updated_at = Ignore()


class ExperienceFactory(SQLModelFactory[Experience], IgnoreAutogeneratedFieldsMixin):
    """Factory for Experience model."""

    __model__ = Experience

    language = Use(SQLModelFactory.__random__.choice, ["fr", "en-GB", "en"])

    @classmethod
    def get_provider_map(cls) -> Dict[Type, Any]:
        """Extend the provider map from the Base class with the IRI type."""
        providers_map = super().get_provider_map()
        return {
            IRI: lambda: f"uuid://{uuid4().hex}",
            **providers_map,
        }

    @classmethod
    def build_dict(cls, exclude=None, json_dump=None, **kwargs) -> dict:
        """Build a dictionary representation of the Experience model.

        Args:
            exclude (set): Set of fields to exclude from the dictionary.
            json_dump (set): Set of fields to convert in a Json string.
            kwargs: Any kwargs matching Experience's fields.

        Returns:
            dict: A dictionary representation of the Experience model.
        """
        if exclude is None:
            exclude = {"id", "created_at", "updated_at"}

        if json_dump is None:
            json_dump = {"title", "technical_datatypes", "description"}

        data = cls.build(**kwargs).dict(exclude=exclude)

        for key in json_dump:
            data[key] = json.dumps(data[key])

        return data


class RelationFactory(SQLModelFactory[Relation], IgnoreAutogeneratedFieldsMixin):
    """Factory for Relation model."""

    __model__ = Relation

    # Ignore foreign keys values
    source_id = Ignore()
    target_id = Ignore()

    @classmethod
    def build(cls, **kwargs):
        """Wrap default build method to handle properly foreign key values.

        Args:
            kwargs: Any kwargs matching Relation's fields.

        Returns:
            Relation: built relation data.
        """
        ExperienceFactory.__session__ = cls.__session__

        # Create experiences for missing foreign keys values
        missing_fk = {"source_id", "target_id"} - kwargs.keys()
        experiences = ExperienceFactory.create_batch_sync(len(missing_fk))

        # Build a relation object with existing source and target in the database
        kwargs.update(
            {
                key: str(experience.id)
                for key, experience in zip(missing_fk, experiences)
            }
        )
        return super().build(**kwargs)
