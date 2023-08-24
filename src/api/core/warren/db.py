"""Warren persistence database connection."""

from sqlmodel import create_engine

from .conf import settings

engine = create_engine(settings.DATABASE_URL, echo=settings.DEBUG)
