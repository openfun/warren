"""Warren API v1."""
from fastapi import FastAPI

from . import video

app = FastAPI()
app.include_router(video.router)
