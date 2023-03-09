"""Warren test fixtures for supported backends."""

import pytest_asyncio
from elasticsearch import AsyncElasticsearch, BadRequestError

from warren.conf import settings


@pytest_asyncio.fixture
async def es():
    """Yields an ElasticSearch test client."""
    client = AsyncElasticsearch(settings.ES_HOSTS)
    try:
        await client.indices.create(index=settings.ES_INDEX)
    except BadRequestError:
        # The index might already exist
        await client.indices.delete(index=settings.ES_INDEX)
        await client.indices.create(index=settings.ES_INDEX)
    yield client
    await client.indices.delete(index=settings.ES_INDEX)
    await client.close()
