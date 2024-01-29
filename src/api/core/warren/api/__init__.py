"""Warren API root."""

from contextlib import asynccontextmanager

import sentry_sdk
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration

from warren.conf import settings
from warren.db import get_engine

from .. import __version__
from .health import router as health_router
from .v1 import app as v1


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application life span."""
    engine = get_engine()
    if settings.SENTRY_DSN is not None:
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            enable_tracing=True,
            traces_sample_rate=settings.SENTRY_API_TRACES_SAMPLE_RATE,
            release=__version__,
            environment=settings.EXECUTION_ENVIRONMENT,
            integrations=[
                StarletteIntegration(),
                FastApiIntegration(),
            ],
        )
    yield
    engine.dispose()


app = FastAPI(lifespan=lifespan)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)

# Health checks
app.include_router(health_router)

# Mount v1 API
app.mount("/api/v1", v1)
