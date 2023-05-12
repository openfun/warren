"""Warren test fixtures for supported backends."""

import pytest
from elasticsearch import AsyncElasticsearch, BadRequestError

from warren import backends
from warren.conf import settings


@pytest.fixture
@pytest.mark.anyio
async def es_client():
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


@pytest.fixture(autouse=True)
@pytest.mark.anyio
async def no_cached_es_client(monkeypatch):
    """Instanciate a new async ES client for all tests.

    Reference:
    https://github.com/elastic/elasticsearch-py/issues/2051
    """
    patched_es_client = AsyncElasticsearch(
        settings.ES_HOSTS, **settings.ES_CLIENT_OPTIONS.dict()
    )
    monkeypatch.setattr(
        backends,
        "es_client",
        patched_es_client,
    )
    yield
    await patched_es_client.close()
