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

    ONE = 1  # smallest level, raw media data or fragments
    TWO = 2  # collection of level 1s, e.g. a lesson
    THREE = 3  # collection of level 2s, e.g. a course
    FOUR = 4  # e.g. set of course that leads to a certificate
