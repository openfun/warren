"""Warren persistence database connection."""

from sqlmodel import Session, create_engine

from .conf import settings

engine = create_engine(settings.DATABASE_URL, echo=settings.DEBUG)


def get_session() -> Session:
    """Get database session single instance."""
    with Session(engine) as session:
        yield session
