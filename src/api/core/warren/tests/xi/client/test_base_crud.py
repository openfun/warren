"""Tests for XI base client."""

from httpx import AsyncClient

from warren.xi.client import BaseCRUD


def test_base_crud_construct_url_with_trailing_slash(http_client: AsyncClient):
    """Test '_construct_url' with a base url which has a trailing slash."""

    class Test(BaseCRUD):
        @property
        def _base_url(self) -> str:
            """Fake base url."""
            return "test/"

        async def create(self, **kwargs) -> None:
            """Placeholder method."""
            raise NotImplementedError

        async def delete(self, **kwargs) -> None:
            """Placeholder method."""
            raise NotImplementedError

        async def get(self, **kwargs) -> None:
            """Placeholder method."""
            raise NotImplementedError

        async def read(self, **kwargs) -> None:
            """Placeholder method."""
            raise NotImplementedError

        async def update(self, **kwargs) -> None:
            """Placeholder method."""
            raise NotImplementedError

    assert (
        Test(client=http_client)._construct_url("uuid://123") == "test/uuid%3A%2F%2F123"
    )


def test_base_crud_construct_url_without_trailing_slash(http_client: AsyncClient):
    """Test '_construct_url' with a base url which has no trailing slash."""

    class Test(BaseCRUD):
        @property
        def _base_url(self) -> str:
            """Fake base url."""
            return "test"

        async def create(self, **kwargs) -> None:
            """Placeholder method."""
            raise NotImplementedError

        async def delete(self, **kwargs) -> None:
            """Placeholder method."""
            raise NotImplementedError

        async def get(self, **kwargs) -> None:
            """Placeholder method."""
            raise NotImplementedError

        async def read(self, **kwargs) -> None:
            """Placeholder method."""
            raise NotImplementedError

        async def update(self, **kwargs) -> None:
            """Placeholder method."""
            raise NotImplementedError

    assert (
        Test(client=http_client)._construct_url("uuid://123") == "test/uuid%3A%2F%2F123"
    )
