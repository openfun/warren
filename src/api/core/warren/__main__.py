#!/usr/bin/env python
"""Warren main entrypoint."""

import sentry_sdk

from . import __version__, cli
from .conf import settings

if settings.SENTRY_DSN is not None:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        traces_sample_rate=settings.SENTRY_CLI_TRACES_SAMPLE_RATE,
        release=__version__,
        environment=settings.EXECUTION_ENVIRONMENT,
        max_breadcrumbs=50,
    )

if __name__ == "__main__":
    cli.cli()
