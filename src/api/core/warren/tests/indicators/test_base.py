"""Test the functions from the BaseIndicator class."""

import pytest
from pytest_httpx import HTTPXMock
from ralph.backends.lrs.base import LRSStatementsQuery

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
            return LRSStatementsQuery(verb="https://w3id.org/xapi/video/verbs/played")

        async def compute(self):
            return None

    my_indicator = MyIndicator()
    my_indicator.lrs_client.base_url = "http://fake-lrs.com"

    # Mock the LRS call so that it returns the fixture statements
    httpx_mock.add_response(
        url="http://fake-lrs.com/xAPI/statements?verb=https://w3id.org/xapi/video/verbs/played&limit=500",
        method="GET",
        json={"statements": [{"id": 1}, {"id": 2}]},
        status_code=200,
    )

    statements = await my_indicator.fetch_statements()
    assert len(statements) == 2


@pytest.mark.anyio
async def test_base_indicator_fetch_statements_with_lrs_failure(
    httpx_mock: HTTPXMock,
):
    """Test the `fetch_statements` method of the base indicator when the LRS
    fails to respond.

    """  # noqa: D205

    class MyIndicator(BaseIndicator):
        def get_lrs_query(self):
            return LRSStatementsQuery(verb="https://w3id.org/xapi/video/verbs/played")

        async def compute(self):
            return None

    my_indicator = MyIndicator()
    my_indicator.lrs_client.base_url = "http://fake-lrs.com"

    # Mock the LRS call so that it returns fails
    httpx_mock.add_response(
        url="http://fake-lrs.com/xAPI/statements?verb=https://w3id.org/xapi/video/verbs/played&limit=500",
        method="GET",
        status_code=500,
    )

    with pytest.raises(LrsClientException):
        await my_indicator.fetch_statements()


def test_base_indicator_replace():
    """Test the base indicator _replace method."""

    class MyIndicator(BaseIndicator):
        def __init__(self, span_range=None, foo=None, bar=None):
            super().__init__(span_range=span_range, foo=foo, bar=bar)

        def get_lrs_query(self):
            return None

        async def compute(self):
            return None

    indicator = MyIndicator(foo="lol", bar=[1, 2, 3])
    assert indicator.span_range is None
    assert indicator.foo == "lol"
    assert indicator.bar == [1, 2, 3]

    # Shallow copy
    copied = indicator._replace(foo="baz", bar=[4, 5, 6])
    assert copied.span_range is None
    assert copied.foo == "baz"
    assert copied.bar == [4, 5, 6]

    # Deep copy
    copied = indicator._replace(deep=True, foo="baz", bar=[4, 5, 6])
    assert copied.span_range is None
    assert copied.foo == "baz"
    assert copied.bar == [4, 5, 6]

    # Proceed by reference to check differences between shallow and deep copies
    bar = [1, 2, 3]
    indicator = MyIndicator(foo="lol", bar=bar)

    shallow = indicator._replace(deep=False, foo="baz")
    deep = indicator._replace(deep=True, foo="baz")
    assert shallow.bar == [1, 2, 3]
    assert deep.bar == [1, 2, 3]

    bar.append(4)
    assert indicator.bar == shallow.bar == [1, 2, 3, 4]
    assert deep.bar == [1, 2, 3]


def test_base_indicator_child_immutability():
    """Check indicators immutability."""

    class MyIndicator(BaseIndicator):
        def __init__(self, span_range=None, foo=None, bar=None):
            super().__init__(span_range=span_range, foo=foo, bar=bar)

        def get_lrs_query(self):
            return None

        async def compute(self):
            return None

    indicator = MyIndicator(foo="lol", bar=[1, 2, 3])

    assert indicator.span_range is None
    assert indicator.foo == "lol"
    assert indicator.bar == [1, 2, 3]

    with pytest.raises(AttributeError, match="Can't set attribute 'span_range'"):
        indicator.span_range = [1, 2]
    with pytest.raises(AttributeError, match="Can't set attribute 'foo'"):
        indicator.foo = "spam"
    with pytest.raises(AttributeError, match="Can't set attribute 'bar'"):
        indicator.bar = 4
    with pytest.raises(AttributeError, match="Can't delete attribute 'span_range'"):
        del indicator.span_range
    with pytest.raises(AttributeError, match="Can't delete attribute 'foo'"):
        del indicator.foo
    with pytest.raises(AttributeError, match="Can't delete attribute 'bar'"):
        del indicator.bar
