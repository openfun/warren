"""Warren persistence database connection."""

from typing import Generator

from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session as SASession
from sqlmodel import Session, create_engine

from .conf import settings

engine = create_engine(settings.DATABASE_URL, echo=settings.DEBUG)


def get_session() -> Generator[Session, None, None]:
    """Get database session single instance."""
    with Session(engine) as session:
        yield session


def is_alive() -> bool:
    """Check if database connection is alive."""
    with SASession(engine) as session:
        try:
            session.execute(text("SELECT 1 as is_alive"))
            return True
        except OperationalError:
            return False
    return False
