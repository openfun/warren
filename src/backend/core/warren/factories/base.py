"""Base factories for xAPI events."""

import uuid
from typing import List

from pydantic import BaseModel


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


class BaseXapiStatementFactory(BaseFactory):
    """Base xAPI Statement factory."""

    @classmethod
    def build(cls, mutations: List[dict] = None) -> None:
        """Force statement id update."""
        instance = super().build(mutations)
        return instance.copy(update={"id": str(uuid.uuid4())})
