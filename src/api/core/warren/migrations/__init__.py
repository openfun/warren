"""Database migrations helpers."""

from alembic import command
from alembic.config import Config

from ..conf import settings

ALEMBIC_CFG: Config = Config(settings.ALEMBIC_CFG_PATH)
ALEMBIC_CFG.set_main_option("sqlalchemy.url", settings.DATABASE_URL)


def current(verbose: bool = False):
    """Get information about the current migration state."""
    command.current(ALEMBIC_CFG, verbose=verbose)


def downgrade(revision: str):
    """Downgrade database schema."""
    command.downgrade(ALEMBIC_CFG, revision)


def history(verbose: bool = False):
    """Get migrations history."""
    command.history(ALEMBIC_CFG, verbose=verbose)


def upgrade(revision: str = "head"):
    """Upgrade database schema."""
    command.upgrade(ALEMBIC_CFG, revision)
