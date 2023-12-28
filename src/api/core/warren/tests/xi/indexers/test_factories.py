"""Tests for indexers and source factories."""


import re
from typing import Optional

import pytest

from warren.xi.indexers.factories import IndexerFactory, SourceFactory


def test_source_factory():
    """Test 'SourceFactory' which instantiates source's clients."""
    factory = SourceFactory()

    # Test that an exception is raised with an unknown key
    with pytest.raises(ValueError, match="No source known for 'foo' key"):
        factory.create("foo")

    class Test:
        foo: str = "foo."

        def __init__(self, name: Optional[str] = None):
            self.name = name

    # Register a class to the factory
    factory.register(Test)

    # Test that an exception is raised with a lowercase key
    with pytest.raises(ValueError, match="No source known for 'test' key"):
        factory.create("test")

    # Create an instance of the 'Test' class through the factory
    source_instance = factory.create("Test")

    # Assert the instance has the expected type
    assert isinstance(source_instance, Test)
    assert source_instance.name is None

    # Create an instance of the 'Test' class with random kwargs
    kwargs = {"name": "john doe"}
    source_instance_with_kwargs = factory.create("Test", **kwargs)

    # Assert the instance has the expected type, and that kwargs were passed
    assert isinstance(source_instance_with_kwargs, Test)
    assert source_instance_with_kwargs.name == "john doe"


@pytest.mark.anyio
async def test_indexer_factory():
    """Test 'IndexerFactory' which instantiates indexers."""
    factory = IndexerFactory()

    class MockedSource:
        foo: str = "foo."

    class MockedTarget:
        foo: str = "foo."

    class MockedIndexer:
        def __init__(self, source, target, name: Optional[str] = None):
            self.source = source
            self.target = target
            self.name = name

        @classmethod
        async def factory(cls, source, target, **kwargs):
            return cls(source, target, **kwargs)

    # Test that an exception is raised with an unknown key
    with pytest.raises(
        ValueError,
        match=re.escape("No indexer known for '('MockedSource', 'foo')' key"),
    ):
        await factory.create(MockedSource(), MockedTarget(), "foo")

    # Register an indexer class to the factory for the 'MockedSource' source
    factory.register(MockedSource, "foo.", MockedIndexer)

    # Create an instance of the 'MockedIndexer' class through the factory
    source = MockedSource()
    target = MockedTarget()
    indexer_instance = await factory.create(source, target, "foo.")

    # Assert the instance has the expected type
    assert isinstance(indexer_instance, MockedIndexer)
    assert indexer_instance.source == source
    assert indexer_instance.target == target
    assert indexer_instance.name is None

    # Create an instance of the 'MockedIndexer' class through the factory passing kwargs
    source = MockedSource()
    target = MockedTarget()
    kwargs = {"name": "john doe"}
    indexer_instance = await factory.create(source, target, "foo.", **kwargs)

    # Assert the instance has the expected type, and that kwargs were passed
    assert isinstance(indexer_instance, MockedIndexer)
    assert indexer_instance.source == source
    assert indexer_instance.target == target
    assert indexer_instance.name == "john doe"
