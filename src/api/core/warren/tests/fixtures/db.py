"""Fixtures for Warren api database."""

import pytest
from alembic import command
from alembic.config import Config
from sqlmodel import Session, SQLModel, create_engine

from warren.api.v1 import app as v1
from warren.conf import settings
from warren.db import get_session
from warren.indicators.mixins import CacheMixin


@pytest.fixture(scope="session")
def db_engine():
    """Test database engine fixture."""
    engine = create_engine(settings.TEST_DATABASE_URL, echo=False)

    # Create database and tables
    SQLModel.metadata.create_all(engine)

    # Pretend to have all migrations applied
    alembic_cfg = Config("core/warren/alembic.ini")
    command.stamp(alembic_cfg, "head")

    yield engine
    SQLModel.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(db_engine):
    """Test session fixture."""
    # Setup
    #
    # Connect to the database and create a non-ORM transaction. Our connection
    # is bound to the test session.
    connection = db_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    yield session

    # Teardown
    #
    # Rollback everything that happened with the Session above (including
    # explicit commits).
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(autouse=True, scope="function")
def force_db_test_session(db_session, monkeypatch):
    """Use test database along with a test session by default."""
    monkeypatch.setattr(CacheMixin, "db_session", db_session)


@pytest.fixture(autouse=True)
def override_db_test_session(db_session):
    """Use test database along with a test session by default."""

    def get_session_override():
        return db_session

    v1.dependency_overrides[get_session] = get_session_override

    yield
