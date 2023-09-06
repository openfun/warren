"""Fixtures for Warren api database."""
import pytest
from alembic import command
from alembic.config import Config
from sqlmodel import Session, SQLModel, create_engine

from warren.conf import settings
from warren.indicators.mixins import CacheMixin


@pytest.fixture(scope="session")
def db_engine():
    """Test database engine fixture."""
    engine = create_engine(settings.TEST_DATABASE_URL, echo=True)

    # Create database and tables
    SQLModel.metadata.create_all(engine)

    # Pretend to have all migrations applied
    alembic_cfg = Config("core/alembic.ini")
    command.stamp(alembic_cfg, "head")

    yield engine
    SQLModel.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(db_engine):
    """Test session fixture."""
    session = Session(db_engine)
    yield session
    session.rollback()
    session.close()


@pytest.fixture(autouse=True, scope="function")
def db_transaction(db_session):
    """Force nested transaction usage."""
    nested = db_session.begin_nested()
    yield nested


@pytest.fixture(autouse=True, scope="function")
def force_db_test_session(db_engine, db_session, monkeypatch):
    """Use test database along with a test session by default."""
    monkeypatch.setattr(CacheMixin, "db_engine", db_engine)
    monkeypatch.setattr(CacheMixin, "db_session", db_session)
