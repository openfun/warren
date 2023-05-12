"""Base factories for xAPI events."""

import uuid
from typing import List

from elasticsearch.helpers import async_bulk
from pydantic import BaseModel

from warren.conf import settings


class BaseFactory:
    """Base factory model."""

    template: dict
    model: BaseModel

    @classmethod
    def build(cls, mutations: List[dict] = None) -> None:
        """Given a template, a model and mutations, return mutated model instance."""
        instance = cls.model.parse_obj(cls.template)
        if mutations is not None:
            for mutation in mutations:
                instance = instance.copy(update=mutation)
        return instance

    @classmethod
    async def save(cls, es_client, instance: BaseModel = None):
        """Save instance to configured backend."""
        await es_client.create(
            id=instance.id,
            index=settings.ES_INDEX,
            refresh=True,
            document=instance.dict(),
        )

    @classmethod
    async def save_many(cls, es_client, instances: List[BaseModel] = None):
        """Save instances to configured backend."""

        async def prepare_documents(instances):
            """Prepare documents for bulk operation."""
            for instance in instances:
                yield {
                    "_id": instance.id,
                    "_index": settings.ES_INDEX,
                    "_op_type": "create",
                    "_source": instance.dict(),
                }

        return await async_bulk(es_client, prepare_documents(instances))


class BaseXapiStatementFactory(BaseFactory):
    """Base xAPI Statement factory."""

    @classmethod
    def build(cls, mutations: List[dict] = None) -> None:
        """Force statement id update."""
        instance = super().build(mutations)
        return instance.copy(update={"id": str(uuid.uuid4())})
