"""Database migrations helpers."""

from pathlib import Path

from alembic import command
from alembic.config import Config

ROOT_PATH: Path = Path(__file__).parent.parent
ALEMBIC_CFG: Config = Config(ROOT_PATH / "alembic.ini")


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
