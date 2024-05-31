"""Experience Index HTTP client."""

import json
import logging
from abc import ABC, abstractmethod
from http import HTTPStatus
from pathlib import PurePath
from typing import List, Optional, Protocol, Tuple, Union
from urllib.parse import quote_plus
from uuid import UUID

from httpx import AsyncClient
from pydantic import UUID4, parse_obj_as

from warren.conf import settings
from warren.fields import IRI
from warren.models import LTIUser
from warren.utils import forge_lti_token

from .enums import (
    RelationType,
)
from .models import (
    ExperienceCreate,
    ExperienceRead,
    ExperienceReadSnapshot,
    ExperienceUpdate,
    RelationCreate,
    RelationRead,
    RelationUpdate,
)

logger = logging.getLogger(__name__)


class Client(Protocol):
    """Protocol for declaring a custom asynchronous client."""

    _client: AsyncClient

    async def close(self):
        """Close client pool of connections asynchronously."""
        ...


class BaseCRUD(ABC):
    """Abstract base class for CRUD operations.

    This class defines the basic structure for performing CRUD
    (Create, Read, Update, Delete) operations on entities using an AsyncClient.
    """

    _client: AsyncClient
    _base_url: str

    def __init__(self, client: AsyncClient):
        """Initialize the base class with an AsyncClient instance."""
        self._client = client

    def _construct_url(self, path: Union[str, UUID, IRI]) -> str:
        """Construct a URL by appending the path to the base URL.

        Args:
            path (Union[str, UUID, str]): The path used for constructing the URL.
                It may contain an IRI which could include double slashes.

        Returns:
            str: The constructed URL.
        """
        return str(PurePath(self._base_url).joinpath(quote_plus(str(path))))

    @abstractmethod
    async def create(self, data):
        """Abstract method for creating an entity."""

    @abstractmethod
    async def get(self, object_id):
        """Abstract method for getting an entity."""

    @abstractmethod
    async def update(self, object_id, data):
        """Abstract method for updating an entity."""

    @abstractmethod
    async def read(self, **kwargs):
        """Abstract method for reading entities."""

    @abstractmethod
    async def delete(self, **kwargs):
        """Abstract method for deleting an entity."""


class CRUDExperience(BaseCRUD):
    """Handle asynchronous CRUD operations on experiences."""

    _base_url: str = "experiences"

    async def create(self, data: ExperienceCreate) -> ExperienceRead:
        """Create an experience.

        Note that as we create a new Relation, the return value cannot be None.
        """
        response = await self._client.post(
            url=self._construct_url(""),
            json=json.loads(data.json()),
        )
        response.raise_for_status()
        object_id = UUID(response.json())
        return await self.get(object_id)  # type: ignore[return-value]

    async def _get_experience_from_iri(self, iri) -> Union[ExperienceRead, None]:
        """Get an experience from its IRI."""
        # Filter experience by URI to get the experience ID
        experiences = await self.read(iri=iri)
        if not len(experiences):
            return None
        experience = experiences.pop()
        return await self.get(experience.id)

    async def get(self, object_id: Union[UUID, IRI]) -> Union[ExperienceRead, None]:
        """Get an experience from one of its identifiers."""
        # Try to cast input string as an UUID
        if isinstance(object_id, str):
            try:
                object_id = UUID4(object_id)
            except ValueError:
                logger.debug(f"Object ID `{object_id}` is not a valid UUID4")
                pass
        if not isinstance(object_id, UUID):
            return await self._get_experience_from_iri(object_id)

        response = await self._client.get(url=self._construct_url(object_id))

        if response.status_code == HTTPStatus.NOT_FOUND:
            return None

        response.raise_for_status()
        return ExperienceRead(**response.json())

    async def update(self, object_id: UUID, data: ExperienceUpdate) -> ExperienceRead:
        """Update an experience."""
        response = await self._client.put(
            url=self._construct_url(object_id),
            json=json.loads(data.json()),
        )
        response.raise_for_status()
        return ExperienceRead(**response.json())

    async def read(self, **kwargs) -> List[ExperienceReadSnapshot]:
        """Read multiple experiences while applying query params."""
        response = await self._client.get(url=self._construct_url(""), params=kwargs)
        response.raise_for_status()
        return parse_obj_as(List[ExperienceReadSnapshot], response.json())

    async def delete(self, **kwargs) -> None:
        """Delete an experience."""
        raise NotImplementedError

    async def create_or_update(self, data: ExperienceCreate) -> ExperienceRead:
        """Create or update an experience depending on its existence."""
        db_experience = await self.get(data.iri)

        if db_experience is None:
            return await self.create(data)

        return await self.update(db_experience.id, ExperienceUpdate(**data.dict()))


class CRUDRelation(BaseCRUD):
    """Handle asynchronous CRUD operations on relations."""

    _base_url: str = "relations"

    async def create(self, data: RelationCreate) -> RelationRead:
        """Create a relation.

        Note that as we create a new Relation, the return value cannot be None.
        """
        response = await self._client.post(
            url=self._construct_url(""),
            json=json.loads(data.json()),
        )
        response.raise_for_status()
        object_id = UUID(response.json())
        return await self.get(object_id)  # type: ignore[return-value]

    async def get(self, object_id: UUID) -> Union[RelationRead, None]:
        """Get a relation from its ID."""
        response = await self._client.get(url=self._construct_url(object_id))

        if response.status_code == HTTPStatus.NOT_FOUND:
            return None

        response.raise_for_status()
        return RelationRead(**response.json())

    async def update(
        self, object_id: UUID, data: Union[RelationUpdate, RelationCreate]
    ) -> RelationRead:
        """Update a relation."""
        response = await self._client.put(
            url=self._construct_url(object_id),
            json=json.loads(data.json()),
        )
        response.raise_for_status()
        return RelationRead(**response.json())

    async def read(self, **kwargs) -> List[RelationRead]:
        """Read multiple relations while applying query params."""
        response = await self._client.get(url=self._construct_url(""), params=kwargs)
        response.raise_for_status()
        return parse_obj_as(List[RelationRead], response.json())

    async def delete(self, **kwargs) -> None:
        """Delete a relation."""
        raise NotImplementedError

    async def create_or_update(self, data: RelationCreate) -> RelationRead:
        """Create a relation."""
        db_relations = await self.read(
            source=data.source_id, target=data.target_id, kind=data.kind.value
        )

        # Create
        if db_relations is None or len(db_relations) == 0:
            return await self.create(data)

        # Update
        db_relation = db_relations.pop()
        return await self.update(
            db_relation.id,
            RelationUpdate(**data.dict()),
        )

    async def create_bidirectional(
        self, source_id: UUID, target_id: UUID, kinds: Tuple[RelationType, RelationType]
    ) -> Tuple[RelationRead, RelationRead]:
        """Create bidirectional relations between two experiences."""
        kind, inverted_kind = kinds

        relation_create = RelationCreate(
            source_id=source_id, target_id=target_id, kind=kind
        )
        inverted_relation_create = RelationCreate(
            source_id=target_id, target_id=source_id, kind=inverted_kind
        )
        relation = await self.create_or_update(relation_create)
        inverted_relation = await self.create_or_update(inverted_relation_create)

        return relation, inverted_relation


class ExperienceIndex(Client):
    """A client to interact with the Experience Index.

    This class encapsulates functionalities to handle CRUD operations on
    experiences and relations via HTTP requests.

    Attributes:
        experience (CRUDExperience): An instance of CRUDExperience.
        relation (CRUDRelation): An instance of CRUDRelation.
    """

    experience: CRUDExperience
    relation: CRUDRelation

    def __init__(self, url: Optional[str] = None):
        """Initialize the asynchronous HTTP client."""
        self._url = url or settings.XI_BASE_URL

        token = forge_lti_token(
            user=LTIUser(
                id="xi",
                email="xi@fake-lms.com",
            ),
            roles=("administrator",),
            consumer_site="https://fake-lms.com",
            course_id="all",
        )
        self._client = AsyncClient(
            base_url=self._url,
            headers={"Authorization": f"Bearer {token}"},
            follow_redirects=True,
        )

        self.experience = CRUDExperience(client=self._client)
        self.relation = CRUDRelation(client=self._client)

    async def close(self):
        """Close the asynchronous HTTP client."""
        await self._client.aclose()
