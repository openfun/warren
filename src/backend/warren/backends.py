"""Backends for warren."""

from elasticsearch import AsyncElasticsearch

from warren.conf import settings

es_client = AsyncElasticsearch(settings.ES_HOSTS, **settings.ES_CLIENT_OPTIONS.dict())
