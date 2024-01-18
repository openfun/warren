"""Experience Index HTTP client."""

from abc import ABC, abstractmethod
from http import HTTPStatus
from os.path import join
from typing import List, Optional, Protocol, Tuple, Union
from urllib.parse import quote_plus
from uuid import UUID

from httpx import AsyncClient
from pydantic import parse_obj_as

from warren.conf import settings
from warren.fields import IRI

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
from .schema import (
    Experience,
    Relation,
)


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
        return join(self._base_url, quote_plus(str(path)))

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

    async def create(self, data: ExperienceCreate) -> UUID:
        """Create an experience."""
        response = await self._client.post(
            url=self._construct_url(""), data=data.json()  # type: ignore[arg-type]
        )
        response.raise_for_status()
        return UUID(response.json())

    async def get(self, object_id: Union[UUID, IRI]) -> Union[ExperienceRead, None]:
        """Get an experience from one of its identifiers."""
        response = await self._client.get(url=self._construct_url(object_id))

        if response.status_code == HTTPStatus.NOT_FOUND:
            return None

        response.raise_for_status()
        return ExperienceRead.construct(**response.json())

    async def update(
        self, object_id: UUID, data: Union[ExperienceUpdate, ExperienceCreate]
    ) -> Experience:
        """Update an experience."""
        response = await self._client.put(
            url=self._construct_url(object_id), data=data.json()  # type: ignore[arg-type]
        )
        response.raise_for_status()
        return Experience(**response.json())

    async def read(self, **kwargs) -> List[ExperienceReadSnapshot]:
        """Read multiple experiences while applying query params."""
        response = await self._client.get(url=self._construct_url(""), params=kwargs)
        response.raise_for_status()
        return parse_obj_as(List[ExperienceReadSnapshot], response.json())

    async def delete(self, **kwargs) -> None:
        """Delete an experience."""
        raise NotImplementedError

    async def create_or_update(self, data: ExperienceCreate) -> Union[UUID, Experience]:
        """Create or update an experience depending on its existence."""
        db_experience = await self.get(data.iri)

        if db_experience is None:
            return await self.create(data)

        return await self.update(db_experience.id, data)


class CRUDRelation(BaseCRUD):
    """Handle asynchronous CRUD operations on relations."""

    _base_url: str = "relations"

    async def create(self, data: RelationCreate) -> UUID:
        """Create a relation."""
        response = await self._client.post(
            url=self._construct_url(""), data=data.json()  # type: ignore[arg-type]
        )
        response.raise_for_status()
        return UUID(response.json())

    async def get(self, object_id: UUID) -> Union[RelationRead, None]:
        """Get a relation from its ID."""
        response = await self._client.get(url=self._construct_url(object_id))

        if response.status_code == HTTPStatus.NOT_FOUND:
            return None

        response.raise_for_status()
        return RelationRead.construct(**response.json())

    async def update(
        self, object_id: UUID, data: Union[RelationUpdate, RelationCreate]
    ) -> Relation:
        """Update a relation."""
        response = await self._client.put(
            url=self._construct_url(object_id), data=data.json()  # type: ignore[arg-type]
        )
        response.raise_for_status()
        return Relation(**response.json())

    async def read(self, **kwargs) -> List[RelationRead]:
        """Read multiple relations while applying query params."""
        response = await self._client.get(url=self._construct_url(""), params=kwargs)
        response.raise_for_status()
        return parse_obj_as(List[RelationRead], response.json())

    async def delete(self, **kwargs) -> None:
        """Delete a relation."""
        raise NotImplementedError

    async def create_bidirectional(
        self, source_id: UUID, target_id: UUID, kinds: Tuple[RelationType, RelationType]
    ) -> Tuple[UUID, UUID]:
        """Create bidirectional relations between two experiences."""
        kind, inverted_kind = kinds

        relation = RelationCreate(source_id=source_id, target_id=target_id, kind=kind)

        inverted_relation = RelationCreate(
            source_id=target_id, target_id=source_id, kind=inverted_kind
        )

        relation_id = await self.create(relation)
        inverted_relation_id = await self.create(inverted_relation)

        return relation_id, inverted_relation_id


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

        self._client = AsyncClient(
            base_url=self._url,
        )

        self.experience = CRUDExperience(client=self._client)
        self.relation = CRUDRelation(client=self._client)

    async def close(self):
        """Close the asynchronous HTTP client."""
        await self._client.aclose()
