"""Warren API v1 video router."""

from fastapi import APIRouter
from warren_video.viewers import router as viewers_router
from warren_video.views import router as views_router

router = APIRouter(prefix="/video", tags=["video"])

router.include_router(views_router)
router.include_router(viewers_router)
