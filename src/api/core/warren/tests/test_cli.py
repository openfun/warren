"""Test Warren commands functions."""
from unittest.mock import AsyncMock, MagicMock

import pytest
from alembic import command as alembic_command
from click import BadParameter
from click.testing import CliRunner
from pydantic import BaseModel
from warren_video.indicators import DailyUniqueCompletedViews

from warren import migrations
from warren.cli import _get_indicator, _get_indicator_entrypoints, cli


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


def test_get_indicator_entrypoints():
    """Test _get_indicator_entrypoints utility."""
    assert [
        "daily_completed_views",
        "daily_downloads",
        "daily_unique_completed_views",
        "daily_unique_downloads",
        "daily_unique_views",
        "daily_views",
    ] == [e.name for e in _get_indicator_entrypoints()]


def test_get_indicator():
    """Test _get_indicator utility."""
    entry_point = _get_indicator("warren_video.indicators:DailyCompletedViews")
    assert entry_point.name == "daily_completed_views"

    entry_point = _get_indicator("warren_video.indicators:DailyUniqueDownloads")
    assert entry_point.name == "daily_unique_downloads"

    with pytest.raises(BadParameter, match='Indicator "foo" is not registered.'):
        _get_indicator("foo")


def test_indicator_list_command():
    """Test warren indicator list command."""
    runner = CliRunner()
    result = runner.invoke(cli, ["indicator", "list"])
    assert (
        "warren_video.indicators:DailyCompletedViews\n"
        "warren_video.indicators:DailyDownloads\n"
        "warren_video.indicators:DailyUniqueCompletedViews\n"
        "warren_video.indicators:DailyUniqueDownloads\n"
        "warren_video.indicators:DailyUniqueViews\n"
        "warren_video.indicators:DailyViews\n"
    ) == result.output


def test_indicator_inspect_command(monkeypatch):
    """Test warren indicator inspect command."""
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["indicator", "inspect", "warren_video.indicators:DailyUniqueCompletedViews"],
    )
    assert (
        "video_id\tPOSITIONAL_OR_KEYWORD\tdefault='no'\t<class 'str'>\n"
        "span_range\tPOSITIONAL_OR_KEYWORD\tdefault='no'\t"
        "<class 'warren.filters.DatetimeRange'>\n"
    ) == result.output

    # Test parameter default value
    def init_mock(self, foo: int = 1):
        pass

    monkeypatch.setattr(DailyUniqueCompletedViews, "__init__", init_mock)

    result = runner.invoke(
        cli,
        ["indicator", "inspect", "warren_video.indicators:DailyUniqueCompletedViews"],
    )
    assert ("foo\tPOSITIONAL_OR_KEYWORD\tdefault=1\t<class 'int'>\n") == result.output


def test_indicator_compute_command_usage():
    """Test warren indicator compute command usage."""
    runner = CliRunner()

    # Test missing parameter
    result = runner.invoke(
        cli,
        [
            "indicator",
            "compute",
            "warren_video.indicators:DailyUniqueCompletedViews",
            'video_id="uuid://foo"',
        ],
    )
    assert result.exit_code == 2
    assert "Parameters are missing" in result.output

    # Test unknown parameter
    result = runner.invoke(
        cli,
        [
            "indicator",
            "compute",
            "warren_video.indicators:DailyUniqueCompletedViews",
            'video_id="uuid://foo"',
            "foo=1",
        ],
    )
    assert result.exit_code == 2
    assert 'Unknown indicator parameter "foo"' in result.output


def test_indicator_compute_command_for_standard_type_return(monkeypatch):
    """Test warren indicator compute command for standard type return."""
    runner = CliRunner()

    # Test return value for a standard type
    async def compute(self) -> dict:
        return {"foo": 1}

    monkeypatch.setattr(DailyUniqueCompletedViews, "compute", compute)
    result = runner.invoke(
        cli,
        [
            "indicator",
            "compute",
            "warren_video.indicators:DailyUniqueCompletedViews",
            'video_id="uuid://foo"',
            "span_range={}",
        ],
    )
    assert "{'foo': 1}\n" == result.output


def test_indicator_compute_command_for_pydantic_type_return(monkeypatch):
    """Test warren indicator compute command for pydantic model return."""
    runner = CliRunner()

    # Test return value for a Pydantic model
    class Fake(BaseModel):
        foo: int

    async def compute(self) -> Fake:
        return Fake(foo=1)

    monkeypatch.setattr(DailyUniqueCompletedViews, "compute", compute)
    result = runner.invoke(
        cli,
        [
            "indicator",
            "compute",
            "warren_video.indicators:DailyUniqueCompletedViews",
            'video_id="uuid://foo"',
            "span_range={}",
        ],
    )
    assert '{"foo": 1}\n' == result.output


def test_indicator_compute_command_no_annotated_type_return(monkeypatch):
    """Test warren indicator compute command for no return annotation."""
    runner = CliRunner()

    # Test invalid compute implementation (no annotations)
    async def compute(self):
        pass

    monkeypatch.setattr(DailyUniqueCompletedViews, "compute", compute)
    result = runner.invoke(
        cli,
        [
            "indicator",
            "compute",
            "warren_video.indicators:DailyUniqueCompletedViews",
            'video_id="uuid://foo"',
            "span_range={}",
        ],
    )
    assert result.exit_code == 2
    assert (
        "Indicator compute method return should be annotated to run from the CLI"
        in result.output
    )


def test_indicator_compute_command_for_not_annotated_indicator(monkeypatch):
    """Test warren indicator compute command for an indicator that is not annotated."""
    runner = CliRunner()

    def init_mock(self, foo):
        pass

    monkeypatch.setattr(DailyUniqueCompletedViews, "__init__", init_mock)
    result = runner.invoke(
        cli,
        [
            "indicator",
            "compute",
            "warren_video.indicators:DailyUniqueCompletedViews",
            "foo=1",
        ],
    )
    assert result.exit_code == 2
    assert (
        "Indicator parameters should be annotated to run from the CLI" in result.output
    )


def test_indicator_compute_command_with_list_or_dict_parameter(monkeypatch):
    """Test warren indicator compute command for an indicator that is not annotated."""
    runner = CliRunner()

    def init_mock(self, foo: list, bar: dict):
        pass

    async def compute(self) -> dict:
        return {"foo": 1}

    monkeypatch.setattr(DailyUniqueCompletedViews, "__init__", init_mock)
    monkeypatch.setattr(DailyUniqueCompletedViews, "compute", compute)
    result = runner.invoke(
        cli,
        [
            "indicator",
            "compute",
            "warren_video.indicators:DailyUniqueCompletedViews",
            "foo=[1, 2, 3]",
            "bar={}",
        ],
    )
    assert result.exit_code == 0
    assert "{'foo': 1}\n" == result.output


def test_indicator_compute_command_with_cache(monkeypatch):
    """Test warren indicator compute command with cache."""
    runner = CliRunner()

    get_or_compute_mock = AsyncMock()
    monkeypatch.setattr(
        DailyUniqueCompletedViews, "get_or_compute", get_or_compute_mock
    )
    runner.invoke(
        cli,
        [
            "indicator",
            "compute",
            "-c",
            "warren_video.indicators:DailyUniqueCompletedViews",
            'video_id="uuid://foo"',
            "span_range={}",
        ],
    )
    get_or_compute_mock.assert_awaited()
