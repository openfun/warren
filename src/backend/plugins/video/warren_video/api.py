"""Warren API v1 video router."""

from fastapi import APIRouter
from warren_video.indicator.complete_viewers.api import (
    router as complete_viewers_router,
)
from warren_video.indicator.complete_views.api import router as complete_views_router
from warren_video.indicator.viewers.api import router as viewers_router
from warren_video.indicator.views.api import router as views_router

router = APIRouter(prefix="/video", tags=["video"])

router.include_router(views_router)
router.include_router(complete_views_router)
router.include_router(viewers_router)
router.include_router(complete_viewers_router)
