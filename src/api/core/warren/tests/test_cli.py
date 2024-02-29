"""Test Warren commands functions."""

# ruff: noqa: S106
from unittest.mock import AsyncMock, MagicMock

import pytest
from alembic import command as alembic_command
from click import BadParameter
from click.testing import CliRunner
from pydantic import BaseModel
from sqlalchemy import select
from sqlmodel import Session
from warren_video.indicators import DailyUniqueCompletedViews

from warren import migrations
from warren.cli import _get_indicator, _get_indicator_entrypoints, cli
from warren.xi.client import CRUDExperience, ExperienceIndex
from warren.xi.enums import AggregationLevel, RelationType
from warren.xi.factories import ExperienceFactory, RelationFactory
from warren.xi.indexers.moodle.client import Moodle
from warren.xi.indexers.moodle.etl import CourseContent, Courses
from warren.xi.models import ExperienceRead, ExperienceReadSnapshot
from warren.xi.schema import Experience


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


def test_indicator_compute_command_with_iri_parameter(monkeypatch):
    """Test warren indicator compute command for standard type return."""
    runner = CliRunner()

    async def compute(self) -> dict:
        return self.video_id

    monkeypatch.setattr(DailyUniqueCompletedViews, "compute", compute)

    # Test IRI value parameter
    result = runner.invoke(
        cli,
        [
            "indicator",
            "compute",
            "warren_video.indicators:DailyUniqueCompletedViews",
            'video_id="uuid://foo?id=1"',
            "span_range={}",
        ],
    )

    assert result.exit_code == 0
    assert "uuid://foo?id=1\n" == result.output


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


def test_xi_index_courses_command(monkeypatch):
    """Test warren xi index courses command."""
    runner = CliRunner()

    moodle_client_mock = MagicMock(return_value=None)
    xi_client_mock = MagicMock(return_value=None)
    indexer_execute_mock = AsyncMock()
    monkeypatch.setattr(Moodle, "__init__", moodle_client_mock)
    monkeypatch.setattr(ExperienceIndex, "__init__", xi_client_mock)
    monkeypatch.setattr(Courses, "execute", indexer_execute_mock)

    result = runner.invoke(
        cli,
        [
            "xi",
            "index",
            "courses",
            "--xi-url",
            "http://xi.foo.com",
            "--moodle-url",
            "http://moodle.foo.com",
            "--moodle-ws-token",
            "faketoken",
        ],
    )

    assert result.exit_code == 0
    moodle_client_mock.assert_called_with(
        url="http://moodle.foo.com", token="faketoken"
    )
    xi_client_mock.assert_called_with(url="http://xi.foo.com")
    indexer_execute_mock.assert_called()


def test_xi_index_course_content_command(monkeypatch):
    """Test warren xi index course content command."""
    runner = CliRunner()

    moodle_client_mock = MagicMock(return_value=None)
    xi_experience_get_mock = AsyncMock(
        return_value=ExperienceRead(
            **ExperienceFactory.build_dict(
                exclude=set(), id="ce0927fa-5f72-4623-9d29-37ef45c39609"
            )
        )
    )
    indexer_execute_mock = AsyncMock()
    monkeypatch.setattr(Moodle, "__init__", moodle_client_mock)
    monkeypatch.setattr(CRUDExperience, "get", xi_experience_get_mock)
    monkeypatch.setattr(CourseContent, "execute", indexer_execute_mock)

    result = runner.invoke(
        cli,
        [
            "xi",
            "index",
            "content",
            "--xi-url",
            "http://xi.foo.com",
            "--moodle-url",
            "http://moodle.foo.com",
            "--moodle-ws-token",
            "faketoken",
            "ce0927fa-5f72-4623-9d29-37ef45c39609",
        ],
    )

    assert result.exit_code == 0
    moodle_client_mock.assert_called_with(
        url="http://moodle.foo.com", token="faketoken"
    )
    xi_experience_get_mock.assert_called_with(
        object_id="ce0927fa-5f72-4623-9d29-37ef45c39609"
    )
    indexer_execute_mock.assert_called()


def test_xi_index_course_content_command_with_unknown_course(monkeypatch):
    """Test warren xi index course content command when course does not exist."""
    runner = CliRunner()

    moodle_client_mock = MagicMock(return_value=None)
    xi_experience_get_mock = AsyncMock(return_value=None)
    monkeypatch.setattr(Moodle, "__init__", moodle_client_mock)
    monkeypatch.setattr(CRUDExperience, "get", xi_experience_get_mock)

    result = runner.invoke(
        cli,
        [
            "xi",
            "index",
            "content",
            "--xi-url",
            "http://xi.foo.com",
            "--moodle-url",
            "http://moodle.foo.com",
            "--moodle-ws-token",
            "faketoken",
            "fake-course-id",
        ],
    )

    assert result.exit_code == 2
    xi_experience_get_mock.assert_called_with(object_id="fake-course-id")
    assert "Unknown course fake-course-id. It should be indexed first!" in result.output


def test_xi_list_courses_command_when_no_course_exists(monkeypatch):
    """Test warren xi list courses command with no indexed course."""
    runner = CliRunner()

    # No course exists
    xi_experience_read_mock = AsyncMock(return_value=[])
    monkeypatch.setattr(CRUDExperience, "read", xi_experience_read_mock)

    result = runner.invoke(
        cli,
        [
            "xi",
            "list",
            "courses",
            "--xi-url",
            "http://xi.foo.com",
        ],
    )

    assert result.exit_code == 0
    assert result.output == ""
    xi_experience_read_mock.assert_called()


def test_xi_list_courses_command(monkeypatch):
    """Test warren xi list courses command."""
    runner = CliRunner()

    courses = [
        ExperienceReadSnapshot(
            **ExperienceFactory.build_dict(
                exclude=set(), aggregation_level=AggregationLevel.THREE
            )
        ),
        ExperienceReadSnapshot(
            **ExperienceFactory.build_dict(
                exclude=set(), aggregation_level=AggregationLevel.THREE
            )
        ),
        ExperienceReadSnapshot(
            **ExperienceFactory.build_dict(
                exclude=set(), aggregation_level=AggregationLevel.THREE
            )
        ),
    ]
    xi_experience_read_mock = AsyncMock(return_value=courses)
    monkeypatch.setattr(CRUDExperience, "read", xi_experience_read_mock)

    result = runner.invoke(
        cli,
        [
            "xi",
            "list",
            "courses",
            "--xi-url",
            "http://xi.foo.com",
        ],
    )

    assert result.exit_code == 0
    assert result.output == "".join([f"{c.id}\t{c.title}\n" for c in courses])
    xi_experience_read_mock.assert_called()


def test_xi_list_course_content_command_with_unknown_course(monkeypatch):
    """Test warren xi index course content command when course does not exist."""
    runner = CliRunner()

    xi_experience_get_mock = AsyncMock(return_value=None)
    monkeypatch.setattr(CRUDExperience, "get", xi_experience_get_mock)

    result = runner.invoke(
        cli,
        [
            "xi",
            "list",
            "content",
            "--xi-url",
            "http://xi.foo.com",
            "fake-course-id",
        ],
    )

    assert result.exit_code == 2
    xi_experience_get_mock.assert_called_with(object_id="fake-course-id")
    assert "Unknown course fake-course-id. It should be indexed first!" in result.output


def test_xi_list_course_content_command_with_no_content(monkeypatch):
    """Test warren xi list course content command when no content exists."""
    runner = CliRunner()

    course = ExperienceRead(
        **ExperienceFactory.build_dict(
            exclude=set(),
            id="ce0927fa-5f72-4623-9d29-37ef45c39609",
            aggregation_level=AggregationLevel.THREE,
            relations_target=[],
        )
    )
    xi_experience_get_mock = AsyncMock(return_value=course)
    monkeypatch.setattr(CRUDExperience, "get", xi_experience_get_mock)

    result = runner.invoke(
        cli,
        [
            "xi",
            "list",
            "content",
            "--xi-url",
            "http://xi.foo.com",
            "ce0927fa-5f72-4623-9d29-37ef45c39609",
        ],
    )

    assert result.exit_code == 2
    assert (
        "No content indexed for course ce0927fa-5f72-4623-9d29-37ef45c39609"
        in result.output
    )


def test_xi_list_course_content_command(db_session: Session, monkeypatch):
    """Test warren xi list course content command."""
    ExperienceFactory.__session__ = db_session
    RelationFactory.__session__ = db_session

    course = ExperienceFactory.create_sync(aggregation_level=AggregationLevel.THREE)
    RelationFactory.create_batch_sync(5, target_id=course.id, kind=RelationType.HASPART)
    modules = db_session.scalars(
        select(Experience).where(
            Experience.id.in_([t.source_id for t in course.relations_target])
        )
    ).all()
    experiences = iter([course] + modules)

    xi_experience_get_mock = AsyncMock(side_effect=experiences)
    monkeypatch.setattr(CRUDExperience, "get", xi_experience_get_mock)

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "xi",
            "list",
            "content",
            f"{course.id}",
        ],
    )

    assert result.exit_code == 0
    assert result.output == "".join([f"{m.id}\t{m.title}\n" for m in modules])


def test_xi_list_course_content_command_with_outdated_relation(
    db_session: Session, monkeypatch
):
    """Test warren xi list course content command when a course content is outdated."""
    ExperienceFactory.__session__ = db_session
    RelationFactory.__session__ = db_session

    course = ExperienceFactory.create_sync(aggregation_level=AggregationLevel.THREE)
    RelationFactory.create_batch_sync(5, target_id=course.id, kind=RelationType.HASPART)
    first_module = db_session.scalars(
        select(Experience).where(Experience.id == course.relations_target[0].source_id)
    ).one()
    experiences = iter([course, None])

    xi_experience_get_mock = AsyncMock(side_effect=experiences)
    monkeypatch.setattr(CRUDExperience, "get", xi_experience_get_mock)

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "xi",
            "list",
            "content",
            f"{course.id}",
        ],
    )

    assert result.exit_code == 1
    assert (
        f"Cannot find content with id {first_module.id} for course {course.id}"
        in result.output
    )
