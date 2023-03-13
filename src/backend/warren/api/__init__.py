"""Warren API root."""
from fastapi import FastAPI

from ..conf import settings
from .v1 import app as v1

app = FastAPI()

es_client = settings.ES_CLIENT

app.mount("/api/v1", v1)


@app.on_event("shutdown")
async def app_shutdown():
    """Shutdown properly the app."""
    await es_client.close()
