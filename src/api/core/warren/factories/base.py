"""Base factories for xAPI events."""

import uuid
from typing import List

from pydantic import BaseModel
from ralph.models.xapi.base.statements import BaseXapiStatement


class BaseFactory:
    """Base factory model."""

    template: dict
    model: BaseModel

    @classmethod
    def build(cls, mutations: List[dict] = None):
        """Given a template, a model and mutations, return mutated model instance."""
        instance = cls.model.parse_obj(cls.template)
        if mutations is not None:
            for mutation in mutations:
                instance = instance.copy(update=mutation)
        return instance


class BaseXapiStatementFactory(BaseFactory):
    """Base xAPI Statement factory."""

    template: dict = {
        "object": {
            "id": "http://adlnet.gov/expapi/activities/example",
            "definition": {
                "name": {"en-US": "Example Activity"},
                "description": {"en-US": "Example activity description"},
            },
            "objectType": "Activity",
        },
        "actor": {
            "objectType": "Agent",
            "account": {"name": "username", "homePage": "http://fun-mooc.fr"},
        },
        "verb": {
            "id": "http://adlnet.gov/expapi/verbs/completed",
            "display": {"en-US": "completed"},
        },
    }
    model: BaseXapiStatement = BaseXapiStatement

    @classmethod
    def build(cls, mutations: List[dict] = None) -> BaseXapiStatement:
        """Force statement id update."""
        instance = super().build(mutations)
        return instance.copy(update={"id": str(uuid.uuid4())})
