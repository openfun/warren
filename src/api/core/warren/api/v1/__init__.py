"""Warren API v1."""

import logging
import sys

from fastapi import FastAPI

from warren.xi.routers import experiences, relations

if sys.version_info < (3, 10):
    from importlib_metadata import entry_points
else:
    from importlib.metadata import entry_points

logger = logging.getLogger(__name__)

app = FastAPI()

# FIXME - extract the experience index in a dedicated package
app.include_router(experiences.router)
app.include_router(relations.router)

# Load plugin routers
for router in entry_points(group="warren.routers"):
    app.include_router(router.load())
    logger.info("Warren plugin '%s' loaded 🎉", router.name)
