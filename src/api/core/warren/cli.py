"""Warren CLI entrypoint."""
import asyncio
import json
import logging
import sys
from inspect import Parameter, Signature, signature
from typing import Optional

import click
from pydantic import BaseModel

from warren import __version__ as warren_version

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
    for entry_point in _get_indicator_entrypoints():
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
        name, value = arg.split("=")

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
            pass
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
