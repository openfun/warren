"""Test Warren commands functions."""
from unittest.mock import MagicMock

from alembic import command as alembic_command
from click.testing import CliRunner

from warren import migrations
from warren.cli import cli


def test_migration_current_command(monkeypatch):
    """Test warren current command."""
    monkeypatch.setattr(alembic_command, "current", MagicMock())

    runner = CliRunner()
    runner.invoke(cli, ["migration", "current"])
    alembic_command.current.assert_called_with(migrations.ALEMBIC_CFG, verbose=False)

    runner.invoke(cli, ["migration", "current", "-v"])
    alembic_command.current.assert_called_with(migrations.ALEMBIC_CFG, verbose=True)

    runner.invoke(cli, ["migration", "current", "--verbose"])
    alembic_command.current.assert_called_with(migrations.ALEMBIC_CFG, verbose=True)


def test_migration_downgrade_command(monkeypatch):
    """Test warren downgrade command."""
    monkeypatch.setattr(alembic_command, "downgrade", MagicMock())

    runner = CliRunner()
    runner.invoke(cli, ["migration", "downgrade", "123abc"])
    alembic_command.downgrade.assert_called_with(migrations.ALEMBIC_CFG, "123abc")


def test_migration_history_command(monkeypatch):
    """Test warren history command."""
    monkeypatch.setattr(alembic_command, "history", MagicMock())

    runner = CliRunner()
    runner.invoke(cli, ["migration", "history"])
    alembic_command.history.assert_called_with(migrations.ALEMBIC_CFG, verbose=False)

    runner.invoke(cli, ["migration", "history", "-v"])
    alembic_command.history.assert_called_with(migrations.ALEMBIC_CFG, verbose=True)

    runner.invoke(cli, ["migration", "history", "--verbose"])
    alembic_command.history.assert_called_with(migrations.ALEMBIC_CFG, verbose=True)


def test_migration_upgrade_command(monkeypatch):
    """Test warren upgrade command."""
    monkeypatch.setattr(alembic_command, "upgrade", MagicMock())

    runner = CliRunner()
    runner.invoke(cli, ["migration", "upgrade"])
    alembic_command.upgrade.assert_called_with(migrations.ALEMBIC_CFG, "head")

    runner.invoke(cli, ["migration", "upgrade", "123abc"])
    alembic_command.upgrade.assert_called_with(migrations.ALEMBIC_CFG, "123abc")
