"""Experience Index Enums."""

from enum import Enum, IntEnum, unique


@unique
class RelationType(str, Enum):
    """Nature of the relationship between two LOM (experiences)."""

    ISPARTOF = "ispartof"
    HASPART = "haspart"
    ISVERSIONOF = "isversionof"
    HASVERSION = "hasversion"
    ISFORMATOF = "isformatof"
    HASFORMAT = "hasformat"
    REFERENCES = "references"
    ISREFERENCEDBY = "isreferencedby"
    ISBASEDON = "isbasedon"
    ISBASISFOR = "isbasisfor"
    REQUIRES = "requires"
    ISREQUIREDBY = "isrequiredby"


@unique
class Structure(str, Enum):
    """Enumeration of Experience Structures."""

    ATOMIC = "atomic"
    COLLECTION = "collection"
    NETWORKED = "networked"
    HIERARCHICAL = "hierarchical"
    LINEAR = "linear"


@unique
class AggregationLevel(IntEnum):
    """Enumeration of Experience Aggregation Levels."""

    ONE = 1
    TWO = 2
    THREE = 3
    FOUR = 4
