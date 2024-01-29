"""Backends for warren."""

from ralph.backends.data.async_lrs import AsyncLRSDataBackend
from ralph.backends.data.lrs import LRSDataBackendSettings, LRSHeaders

from warren.conf import settings

lrs_client_settings = LRSDataBackendSettings(
    BASE_URL=settings.LRS_HOSTS,
    USERNAME=settings.LRS_AUTH_BASIC_USERNAME,
    PASSWORD=settings.LRS_AUTH_BASIC_PASSWORD,
    HEADERS=LRSHeaders(
        X_EXPERIENCE_API_VERSION="1.0.3", CONTENT_TYPE="application/json"
    ),
)

lrs_client = AsyncLRSDataBackend(settings=lrs_client_settings)
