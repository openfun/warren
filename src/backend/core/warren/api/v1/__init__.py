"""Warren API v1."""
import logging
import sys

from fastapi import FastAPI

if sys.version_info < (3, 10):
    from importlib_metadata import entry_points
else:
    from importlib.metadata import entry_points

logger = logging.getLogger(__name__)

app = FastAPI()

# Load plugin routers
for router in entry_points(group="warren.routers"):
    app.include_router(router.load())
    logger.info("Warren plugin '%s' loaded 🎉", router.name)
