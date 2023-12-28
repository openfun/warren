"""Experience Index indexers factories."""

from ..client import Client


class SourceFactory:
    """Factory class for creating sources.

    This factory class provides a method to create different
    sources based on a source's key.
    """

    def __init__(self):
        """Initialize the source registry."""
        self._source_registry = {}

    def register(self, klass):
        """Register a source class."""
        self._source_registry[klass.__name__] = klass

    def create(self, key, **kwargs):
        """Create a source based on the given key."""
        if key not in self._source_registry:
            raise ValueError(f"No source known for '{key}' key")

        return self._source_registry[key](**kwargs)


class IndexerFactory:
    """Factory class for creating indexers based on args.

    This factory class provides a method to create different indexers
    based on the specified source and indexer key.
    """

    def __init__(self):
        """Initialize the indexer registry."""
        self._indexer_registry = {}

    def register(self, source_klass, key, klass):
        """Register an indexer class."""
        self._indexer_registry[(source_klass.__name__, key)] = klass

    async def create(self, source: Client, target: Client, indexer_key, **kwargs):
        """Create an indexer based on a given key and its source's type.

        Some indexers need async operation to be instanced, eg. read a course
        in the database. The class factory calls indexer's factory method to
        instantiate the indexer properly.
        """
        key = (source.__class__.__name__, indexer_key)

        if key not in self._indexer_registry:
            raise ValueError(f"No indexer known for '{key}' key")

        indexer_klass = self._indexer_registry[key]
        return await indexer_klass.factory(source, target, **kwargs)
