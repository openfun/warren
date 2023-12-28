"""Experience Index indexers runner script."""

import argparse
import asyncio
import logging

from httpx import HTTPError
from pydantic import ValidationError

from warren.xi.client import ExperienceIndex
from warren.xi.indexers.factories import IndexerFactory, SourceFactory
from warren.xi.indexers.moodle.client import Moodle
from warren.xi.indexers.moodle.etl import (
    CourseContent,
    Courses,
)

logger = logging.getLogger(__name__)


# Register all available data sources
source_factory = SourceFactory()
source_factory.register(Moodle)

# Register all available Experience Index (XI) indexers
indexer_factory = IndexerFactory()
indexer_factory.register(Moodle, "courses", Courses)
indexer_factory.register(Moodle, "modules", CourseContent)


async def run_indexer(args):
    """Run an Experience Index (XI) indexer based on provided arguments."""
    target = ExperienceIndex()
    source = source_factory.create(args.source_key)

    try:
        indexer = await indexer_factory.create(source, target, **vars(args))
        logger.debug("Running indexer: %s", indexer)
        await indexer.execute()
    except (HTTPError, ValidationError, ValueError) as err:
        msg = "Runner has stopped"
        logger.exception(msg)
        raise RuntimeError(msg) from err

    finally:
        logger.debug("Closing clients session")
        await source.close()
        await target.close()


if __name__ == "__main__":
    """Main function to run Experience Index (XI) indexers."""

    parser = argparse.ArgumentParser(description="Run Experience Index indexers.")
    parser.add_argument("source_key", type=str, help="Key to specify the source.")
    parser.add_argument(
        "indexer_key",
        type=str,
        help="Key to specify the indexer.",
    )
    parser.add_argument(
        "-ie",
        "--ignore_errors",
        action="store_true",
        help="Flag to stop execution when encountering errors.",
        default=False,
    )
    parser.add_argument("--course_iri", type=str, nargs="?")

    args = parser.parse_args()
    asyncio.run(run_indexer(args))
