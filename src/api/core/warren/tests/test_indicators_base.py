"""Test the functions from the BaseIndicator class."""
import pytest
from pytest_httpx import HTTPXMock
from ralph.backends.http.async_lrs import LRSQuery

from warren.exceptions import LrsClientException
from warren.indicators.base import BaseIndicator


@pytest.mark.anyio
async def test_base_indicator_fetch_statements_with_default_query(
    httpx_mock: HTTPXMock,
):
    """Test the `fetch_statements` method of the base indicator using the default
    LRS query returned by the get_lrs_query() method.

    """  # noqa: D205

    class MyIndicator(BaseIndicator):
        def get_lrs_query(self):
            return LRSQuery(query={"verb": "played"})

        async def compute(self):
            return None

    my_indicator = MyIndicator()
    my_indicator.lrs_client.base_url = "http://fake-lrs.com"

    # Mock the LRS call so that it returns the fixture statements
    httpx_mock.add_response(
        url="http://fake-lrs.com/xAPI/statements?verb=played&limit=500",
        method="GET",
        json={"statements": [{"id": 1}, {"id": 2}]},
        status_code=200,
    )

    statements = await my_indicator.fetch_statements()
    assert len(statements) == 2


@pytest.mark.anyio
async def test_base_indicator_fetch_statements_with_custom_query(
    httpx_mock: HTTPXMock,
):
    """Test the `fetch_statements` method of the base indicator using a custom
    LRS query.

    """  # noqa: D205

    class MyIndicator(BaseIndicator):
        def get_lrs_query(self):
            return LRSQuery(query={"verb": "played"})

        async def compute(self):
            return None

    my_indicator = MyIndicator()
    my_indicator.lrs_client.base_url = "http://fake-lrs.com"

    # Mock the LRS call so that it returns the fixture statements
    httpx_mock.add_response(
        url="http://fake-lrs.com/xAPI/statements?verb=downloaded&limit=0",
        method="GET",
        json={"statements": [{"id": 1}, {"id": 2}, {"id": 3}]},
        status_code=200,
    )

    statements = await my_indicator.fetch_statements(
        lrs_query=LRSQuery(query={"verb": "downloaded", "limit": 0})
    )
    assert len(statements) == 3


@pytest.mark.anyio
async def test_base_indicator_fetch_statements_with_lrs_failure(
    httpx_mock: HTTPXMock,
):
    """Test the `fetch_statements` method of the base indicator when the LRS
    fails to respond.

    """  # noqa: D205

    class MyIndicator(BaseIndicator):
        def get_lrs_query(self):
            return LRSQuery(query={"verb": "played"})

        async def compute(self):
            return None

    my_indicator = MyIndicator()
    my_indicator.lrs_client.base_url = "http://fake-lrs.com"

    # Mock the LRS call so that it returns fails
    httpx_mock.add_response(
        url="http://fake-lrs.com/xAPI/statements?verb=played&limit=500",
        method="GET",
        status_code=500,
    )

    with pytest.raises(LrsClientException):
        await my_indicator.fetch_statements()
