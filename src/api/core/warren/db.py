"""Warren persistence database connection."""
import logging

from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from sqlmodel import Session as SessionBase
from sqlmodel import create_engine

from .conf import settings

logger = logging.getLogger(__name__)


class Singleton(type):
    """Singleton pattern metaclass."""

    _instances = {}

    def __call__(cls, *args, **kwargs):
        """Store instances in a private class property."""
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class Engine(metaclass=Singleton):
    """Database engine singleton."""

    _engine = None

    def get_engine(self, url, echo=False):
        """Get created engine or create a new one."""
        if self._engine is None:
            logger.debug("Create a new engine")
            self._engine = create_engine(url, echo=echo)
        logger.debug("Getting database engine %s", self._engine)
        return self._engine


class Session(metaclass=Singleton):
    """Database session singleton."""

    _session = None

    def get_session(self, engine):
        """Get active session or create a new one."""
        if self._session is None:
            logger.debug("Create new session")
            self._session = SessionBase(bind=engine)
        logger.debug("Getting database session %s", self._session)
        return self._session


def get_engine():
    """Get database engine."""
    return Engine().get_engine(url=settings.DATABASE_URL, echo=settings.DEBUG)


def get_session():
    """Get database session."""
    session = Session().get_session(get_engine())
    logger.debug("Getting session %s", session)
    return session


def is_alive() -> bool:
    """Check if database connection is alive."""
    session = get_session()
    try:
        session.exec(text("SELECT 1 as is_alive"))
        return True
    except OperationalError:
        return False
    return False
