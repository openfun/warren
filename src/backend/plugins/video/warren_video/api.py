"""Warren API v1 video router."""

from fastapi import APIRouter
from warren_video.backend import register_indicator
from warren_video.backend import router as backend_router
from warren_video.indicator.complete_viewers.indicator import complete_viewers_indicator
from warren_video.indicator.complete_views.indicator import complete_views_indicator
from warren_video.indicator.viewers.indicator import viewers_indicator
from warren_video.indicator.views.indicator import views_indicator

router = APIRouter(prefix="/video", tags=["video"])

register_indicator(views_indicator)
register_indicator(complete_views_indicator)
register_indicator(viewers_indicator)
register_indicator(complete_viewers_indicator)

router.include_router(backend_router)
