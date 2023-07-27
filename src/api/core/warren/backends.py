"""Backends for warren."""

from ralph.backends.http import AsyncLRSHTTP
from ralph.conf import LRSHeaders

from warren.conf import settings

lrs_client = AsyncLRSHTTP(
    base_url=settings.LRS_HOSTS,
    username=settings.LRS_AUTH_BASIC_USERNAME,
    password=settings.LRS_AUTH_BASIC_PASSWORD,
    headers=LRSHeaders(
        X_EXPERIENCE_API_VERSION="1.0.3", CONTENT_TYPE="application/json"
    ),
)
