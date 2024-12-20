"""Warren CLI entrypoint."""

import asyncio
import json
import logging
import sys
from inspect import Parameter, Signature, signature
from typing import Optional
from uuid import UUID

import click
from alembic.util import CommandError
from pydantic import BaseModel

from warren import __version__ as warren_version
from warren.xi.client import ExperienceIndex
from warren.xi.enums import AggregationLevel
from warren.xi.indexers.moodle.client import Moodle
from warren.xi.indexers.moodle.etl import (
    CourseContent,
    Courses,
)

from . import migrations as alembic_migrations

if sys.version_info < (3, 10):
    from importlib_metadata import EntryPoint, EntryPoints, entry_points
else:
    from importlib.metadata import EntryPoint, EntryPoints, entry_points

logger = logging.getLogger(__name__)


@click.group(name="Warren")
@click.version_option(version=warren_version)
def cli():
    """Warren command line tool."""


# -- MIGRATION COMMAND --
@cli.group(name="migration")
def migration():
    """Database migration commands (alembic wrapper)."""


@migration.command()
def check():
    """Check database migration."""
    try:
        alembic_migrations.check()
    except CommandError:
        raise click.ClickException("Target database is not up to date.") from None


@migration.command()
@click.option("--verbose", "-v", is_flag=True, default=False)
def current(verbose: bool):
    """Show current database migration."""
    alembic_migrations.current(verbose)


@migration.command()
@click.argument("revision", type=str)
def downgrade(revision: str):
    """Downgrade database migration to a target revision."""
    alembic_migrations.downgrade(revision)


@migration.command()
@click.option("--verbose", "-v", is_flag=True, default=False)
def history(verbose: bool):
    """Show database migrations history."""
    alembic_migrations.history(verbose)


@migration.command()
@click.argument("revision", type=str, default="head")
def upgrade(revision: str):
    """Upgrade database migration to a target revision."""
    alembic_migrations.upgrade(revision)


# -- INDICATOR COMMAND --
@cli.group(name="indicator")
def indicator():
    """Indicator commands."""


def _get_indicator_entrypoints() -> EntryPoints:
    """Get 'warren.indicators' entry points."""
    return entry_points(group="warren.indicators")


def _get_indicator(name: str) -> EntryPoint:
    """Get an indicator from its entry point name."""
    try:
        return next(filter(lambda ep: ep.value == name, _get_indicator_entrypoints()))
    except StopIteration as exc:
        raise click.BadParameter(f'Indicator "{name}" is not registered.') from exc


@indicator.command("list")
def indicator_list():
    """List registered active indicators."""
    # Get and sort the entry points by value in alphabetical order
    sorted_entry_points = sorted(_get_indicator_entrypoints(), key=lambda ep: ep.value)
    for entry_point in sorted_entry_points:
        click.echo(entry_point.value)


@indicator.command("inspect")
@click.argument("indicator")
def indicator_inspect(indicator: str):
    """Show indicator required arguments."""
    entry_point: EntryPoint = _get_indicator(indicator)

    # Load the indicator class
    klass = entry_point.load()
    indicator_signature: Signature = signature(klass)

    for parameter in indicator_signature.parameters.values():
        default = "no"
        if parameter.default != Parameter.empty:
            default = parameter.default
        click.secho(f"{parameter.name}\t", bold=True, fg="cyan", nl=False)
        click.echo(f"{parameter.kind}\t{default=}\t{parameter.annotation}")


@indicator.command(
    "compute",
    context_settings={
        "ignore_unknown_options": True,
        "allow_extra_args": True,
    },
)
@click.pass_context
@click.argument("indicator")
@click.option("--cache", "-c", is_flag=True, default=False)
def indicator_compute(ctx: click.Context, indicator: str, cache: bool):
    """Pre-compute a registered target indicator."""
    entry_point: EntryPoint = _get_indicator(indicator)

    # Load the indicator class
    klass = entry_point.load()
    indicator_signature: Signature = signature(klass)
    compute_annotation = signature(klass.compute).return_annotation

    if compute_annotation == Signature.empty:
        raise click.BadParameter(
            (
                f"{indicator} Indicator compute method return "
                "should be annotated to run from the CLI."
            )
        )

    if len(ctx.args) < len(indicator_signature.parameters):
        raise click.UsageError(
            (
                f"Parameters are missing for the '{indicator}' indicator. "
                "See 'inspect' command output."
            )
        )

    # Parse indicator arguments
    indicator_kwargs: dict = {}
    for arg in ctx.args:
        name, value = arg.split(sep="=", maxsplit=1)

        # Get expected parameter from its name
        parameter: Optional[Parameter] = indicator_signature.parameters.get(name)
        if parameter is None:
            raise click.BadParameter(f'Unknown indicator parameter "{name}".')

        if parameter.annotation == Parameter.empty:
            raise click.BadParameter(
                (
                    f"{parameter}"
                    "Indicator parameters should be annotated to run from the CLI."
                )
            )

        # Cast value given parameter annotation
        if issubclass(parameter.annotation, str):
            value = value.strip('"')
        elif issubclass(parameter.annotation, (dict, list)):
            value = json.loads(value)
        elif issubclass(parameter.annotation, BaseModel):
            value = parameter.annotation.parse_raw(value)
        indicator_kwargs[name] = value

    instance = klass(**indicator_kwargs)
    run = instance.compute
    if cache and hasattr(instance, "cache_key"):
        run = instance.get_or_compute
    result = asyncio.run(run())
    click.echo(
        result.json() if issubclass(compute_annotation, BaseModel) else str(result)
    )


# -- EXPERIENCE INDEX (AKA XI) COMMAND --
@cli.group(name="xi")
def xi():
    """Experience index commands."""


@xi.group("list")
def xi_list():
    """List Experience Index objects."""


@xi_list.command("courses")
@click.option("--xi-url", "-x", default="")
def xi_list_courses(xi_url: str):
    """List indexed LMS courses."""
    xi = ExperienceIndex(url=xi_url)
    experiences = asyncio.run(
        xi.experience.read(aggregation_level=AggregationLevel.THREE)
    )
    for experience in experiences:
        click.echo(f"{experience.id}\t{experience.title}")


async def _xi_list_course_content(course_id: UUID, xi_url: str):
    """List indexed LMS course content.

    Nota bene: as we are calling multiple asynchronous functions, we need
    to wrap calls in a single async function called in a synchronous Click
    command using the asyncio.run method. Calling asyncio.run multiple times
    can close the execution loop unexpectedly.
    """
    xi = ExperienceIndex(url=xi_url)
    # Get the course given its experience UUID
    experience = await xi.experience.get(object_id=course_id)
    if experience is None:
        raise click.BadParameter(
            f"Unknown course {course_id}. It should be indexed first!"
        )
    if not experience.relations_target:
        raise click.BadParameter(f"No content indexed for course {course_id}")
    for source in experience.relations_target:
        content = await xi.experience.get(object_id=source.source_id)
        if content is None:
            raise click.ClickException(
                f"Cannot find content with id {source.source_id} for course {course_id}"
            )
        click.echo(f"{content.id}\t{content.title}")


@xi_list.command("content")
@click.argument("course-id")
@click.option("--xi-url", "-x", default="")
def xi_list_course_content(course_id: UUID, xi_url: str):
    """List indexed LMS course content."""
    asyncio.run(_xi_list_course_content(course_id=course_id, xi_url=xi_url))


@xi.group("index")
def xi_index():
    """Feed the Experience Index with an indexer."""


@xi_index.command("courses")
@click.option("--xi-url", "-x", default="")
@click.option("--moodle-url", "-u", default="")
@click.option("--moodle-ws-token", "-t", default="")
@click.option("--timeout", "-T", type=float, default=None)
@click.option("--ignore-errors/--no-ignore-errors", "-I/-F", default=False)
def xi_index_courses(
    xi_url: str,
    moodle_url: str,
    moodle_ws_token: str,
    timeout: Optional[float],
    ignore_errors: bool,
):
    """Index LMS courses."""
    lms = Moodle(url=moodle_url, token=moodle_ws_token, timeout=timeout)
    xi = ExperienceIndex(url=xi_url)
    indexer = Courses(lms=lms, xi=xi, ignore_errors=ignore_errors)
    asyncio.run(indexer.execute())


async def _xi_index_course_content(  # noqa: PLR0913
    course_id: UUID,
    xi_url: str,
    moodle_url: str,
    moodle_ws_token: str,
    timeout: Optional[float],
    ignore_errors: bool,
):
    """Index LMS course content.

    Nota bene: as we are calling multiple asynchronous functions, we need
    to wrap calls in a single async function called in a synchronous Click
    command using the asyncio.run method. Calling asyncio.run multiple times
    can close the execution loop unexpectedly.
    """
    lms = Moodle(url=moodle_url, token=moodle_ws_token, timeout=timeout)
    xi = ExperienceIndex(url=xi_url)

    # Check if the course has been indexed
    course = await xi.experience.get(object_id=course_id)
    if course is None:
        raise click.BadParameter(
            f"Unknown course {course_id}. It should be indexed first!"
        )

    indexer = CourseContent(course=course, lms=lms, xi=xi, ignore_errors=ignore_errors)
    await indexer.execute()


@xi_index.command("content")
@click.argument("course-id")
@click.option("--xi-url", "-x", default="")
@click.option("--moodle-url", "-u", default="")
@click.option("--moodle-ws-token", "-t", default="")
@click.option("--timeout", "-T", type=float, default=None)
@click.option("--ignore-errors/--no-ignore-errors", "-I/-F", default=False)
def xi_index_course_content(  # noqa: PLR0913
    course_id: UUID,
    xi_url: str,
    moodle_url: str,
    moodle_ws_token: str,
    timeout: Optional[float],
    ignore_errors: bool,
):
    """Index LMS content of a course."""
    asyncio.run(
        _xi_index_course_content(
            course_id, xi_url, moodle_url, moodle_ws_token, timeout, ignore_errors
        )
    )


async def _xi_index_all(
    xi_url: str,
    moodle_url: str,
    moodle_ws_token: str,
    timeout: Optional[float],
    ignore_errors: bool,
):
    """Index LMS courses and their content.

    Nota bene: as we are calling multiple asynchronous functions, we need
    to wrap calls in a single async function called in a synchronous Click
    command using the asyncio.run method. Calling asyncio.run multiple times
    can close the execution loop unexpectedly.
    """
    lms = Moodle(url=moodle_url, token=moodle_ws_token, timeout=timeout)
    xi = ExperienceIndex(url=xi_url)

    indexer_courses = Courses(lms=lms, xi=xi, ignore_errors=ignore_errors)
    await indexer_courses.execute()

    experiences = await xi.experience.read(aggregation_level=AggregationLevel.THREE)
    for experience in experiences:
        course = await xi.experience.get(object_id=experience.id)
        if course is None:
            raise click.BadParameter(
                f"Unknown course {experience.id}. Course indexation has failed!"
            )
        indexer_content = CourseContent(
            course=course, lms=lms, xi=xi, ignore_errors=ignore_errors
        )
        await indexer_content.execute()


@xi_index.command("all")
@click.option("--xi-url", "-x", default="")
@click.option("--moodle-url", "-u", default="")
@click.option("--moodle-ws-token", "-t", default="")
@click.option("--timeout", "-T", type=float, default=None)
@click.option("--ignore-errors/--no-ignore-errors", "-I/-F", default=False)
def xi_index_all(
    xi_url: str,
    moodle_url: str,
    moodle_ws_token: str,
    timeout: Optional[float],
    ignore_errors: bool,
):
    """Index all LMS courses and their content."""
    asyncio.run(
        _xi_index_all(xi_url, moodle_url, moodle_ws_token, timeout, ignore_errors)
    )
