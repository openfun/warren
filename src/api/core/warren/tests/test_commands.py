"""Test Warren commands functions."""

import sys
from unittest.mock import MagicMock

import pytest
from alembic import command as alembic_command

from warren import commands, migrations


def test_get_command_line_parser(capsys):
    """Test warren commands parser."""
    parser = commands.get_command_line_parser()

    # No argument passed
    parsed = parser.parse_args([])
    assert vars(parsed) == {}

    # Unkown argument should raise a SystemExit error
    with pytest.raises(SystemExit):
        parser.parse_args(["-foo"])
    captured = capsys.readouterr()
    assert "unrecognized arguments: -foo" in captured.err

    # Unkown command should raise a SystemExit error
    with pytest.raises(SystemExit):
        parser.parse_args(["foo"])
    captured = capsys.readouterr()
    assert "invalid choice: 'foo'" in captured.err

    # Command: current
    parsed = parser.parse_args(["current"])
    assert parsed.verbose is False
    assert parsed.func == migrations.current

    parsed = parser.parse_args(["current", "-v"])
    assert parsed.verbose is True
    assert parsed.func == migrations.current

    parsed = parser.parse_args(["current", "--verbose"])
    assert parsed.verbose is True
    assert parsed.func == migrations.current

    # Command: downgrade
    with pytest.raises(SystemExit):
        parser.parse_args(["downgrade"])
    captured = capsys.readouterr()
    assert "the following arguments are required: revision" in captured.err

    parsed = parser.parse_args(["downgrade", "123abc"])
    assert parsed.revision == "123abc"
    assert parsed.func == migrations.downgrade

    # Command: history
    parsed = parser.parse_args(["history"])
    assert parsed.verbose is False
    assert parsed.func == migrations.history

    parsed = parser.parse_args(["history", "-v"])
    assert parsed.verbose is True
    assert parsed.func == migrations.history

    parsed = parser.parse_args(["history", "--verbose"])
    assert parsed.verbose is True
    assert parsed.func == migrations.history

    # Command: upgrade
    parsed = parser.parse_args(["upgrade"])
    assert parsed.revision == "head"
    assert parsed.func == migrations.upgrade

    parsed = parser.parse_args(["upgrade", "123abc"])
    assert parsed.revision == "123abc"
    assert parsed.func == migrations.upgrade


@pytest.mark.parametrize(
    "cmd",
    [
        [],
        None,
    ],
)
def test_warren_command(capsys, monkeypatch, cmd):
    """Test warren command call without subcommands."""
    monkeypatch.setattr(sys, "argv", [])
    commands.main(cmd)
    captured = capsys.readouterr()
    assert captured.out.startswith(
        "usage: warren [-h] {current,downgrade,history,upgrade}"
    )


@pytest.mark.parametrize(
    "argv,expected",
    [
        (["warren"], "usage: warren [-h] {current,downgrade,history,upgrade}"),
        (["warren", "-h"], "usage: warren [-h] {current,downgrade,history,upgrade}"),
        (["warren", "current", "-h"], "usage: warren current [-h] [-v]"),
        (["warren", "downgrade", "-h"], "usage: warren downgrade [-h] revision"),
        (["warren", "history", "-h"], "usage: warren history [-h] [-v]"),
        (["warren", "upgrade", "-h"], "usage: warren upgrade [-h] [revision]"),
    ],
)
def test_warren_command_defaults_to_sys_argv(capsys, monkeypatch, argv, expected):
    """Test the warren command defaults to sys.argv while parsing args."""
    monkeypatch.setattr(sys, "argv", argv)
    try:
        commands.main()
    except SystemExit as exc:
        if exc.code != 0:
            raise exc
    captured = capsys.readouterr()
    assert captured.out.startswith(expected)


def test_current_command(monkeypatch):
    """Test warren current command."""
    monkeypatch.setattr(alembic_command, "current", MagicMock())

    commands.main(["current"])
    alembic_command.current.assert_called_with(migrations.ALEMBIC_CFG, verbose=False)

    commands.main(["current", "-v"])
    alembic_command.current.assert_called_with(migrations.ALEMBIC_CFG, verbose=True)

    commands.main(["current", "--verbose"])
    alembic_command.current.assert_called_with(migrations.ALEMBIC_CFG, verbose=True)


def test_downgrade_command(monkeypatch):
    """Test warren downgrade command."""
    monkeypatch.setattr(alembic_command, "downgrade", MagicMock())

    commands.main(["downgrade", "123abc"])
    alembic_command.downgrade.assert_called_with(migrations.ALEMBIC_CFG, "123abc")


def test_history_command(monkeypatch):
    """Test warren history command."""
    monkeypatch.setattr(alembic_command, "history", MagicMock())

    commands.main(["history"])
    alembic_command.history.assert_called_with(migrations.ALEMBIC_CFG, verbose=False)

    commands.main(["history", "-v"])
    alembic_command.history.assert_called_with(migrations.ALEMBIC_CFG, verbose=True)

    commands.main(["history", "--verbose"])
    alembic_command.history.assert_called_with(migrations.ALEMBIC_CFG, verbose=True)


def test_upgrade_command(monkeypatch):
    """Test warren upgrade command."""
    monkeypatch.setattr(alembic_command, "upgrade", MagicMock())

    commands.main(["upgrade"])
    alembic_command.upgrade.assert_called_with(migrations.ALEMBIC_CFG, "head")

    commands.main(["upgrade", "123abc"])
    alembic_command.upgrade.assert_called_with(migrations.ALEMBIC_CFG, "123abc")
