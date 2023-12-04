"""Warren API root."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from warren.conf import settings
from warren.db import get_engine

from .health import router as health_router
from .v1 import app as v1


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application life span."""
    engine = get_engine()
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
