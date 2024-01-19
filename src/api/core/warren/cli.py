"""Warren CLI entrypoint."""
import click

from warren import __version__ as warren_version

from . import migrations as alembic_migrations


@click.group(name="Warren")
@click.version_option(version=warren_version)
def cli():
    """Warren command line tool."""


# -- MIGRATION COMMAND --
@cli.group(name="migration")
def migration():
    """Database migration commands (alembic wrapper)."""


@migration.command()
@click.option("--verbose", "-v", is_flag=True, default=False)
def current(verbose):
    """Show current database migration."""
    alembic_migrations.current(verbose)


@migration.command()
@click.argument("revision", type=str)
def downgrade(revision):
    """Downgrade database migration to a target revision."""
    alembic_migrations.downgrade(revision)


@migration.command()
@click.option("--verbose", "-v", is_flag=True, default=False)
def history(verbose):
    """Show database migrations history."""
    alembic_migrations.history(verbose)


@migration.command()
@click.argument("revision", type=str, default="head")
def upgrade(revision):
    """Upgrade database migration to a target revision."""
    alembic_migrations.upgrade(revision)
