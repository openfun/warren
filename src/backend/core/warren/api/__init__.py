"""Warren API root."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from warren.conf import settings

from .. import backends
from .v1 import app as v1


# pylint: disable=redefined-outer-name,unused-argument
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application lifespan."""
    # Startup actions goes here
    # [...]

    # We are now ready
    yield

    # Properly shutdown the application
    await backends.es_client.close()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.mount("/api/v1", v1)