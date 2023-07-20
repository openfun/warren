"""Warren model fields."""

import datetime

import arrow
import rfc3987


class Date():
    """Arrow-parser-based date field."""

    @classmethod
    def __get_validators__(cls):
        """Yields default class validator."""
        yield cls.validate

    @classmethod
    def validate(cls, value) -> datetime.date:
        """Parse arrow-compatible date string."""
        if isinstance(value, datetime.date):
            return value
        if isinstance(value, arrow.Arrow):
            return value.date()
        try:
            return arrow.get(value).date()
        except arrow.ParserError as err:
            raise ValueError("Invalid input date") from err

    @classmethod
    def __modify_schema__(cls, field_schema):
        """Make field JSON schema serializable."""
        field_schema.update(type="string", example="2023-01-01")


class Datetime():
    """Arrow-parser-based date/time field."""

    @classmethod
    def __get_validators__(cls):
        """Yields default class validator."""
        yield cls.validate

    @classmethod
    def validate(cls, value) -> datetime.datetime:
        """Parse arrow-compatible date/time string."""
        if isinstance(value, datetime.datetime):
            return value
        if isinstance(value, arrow.Arrow):
            return value.datetime
        try:
            return arrow.get(value).datetime
        except arrow.ParserError as err:
            raise ValueError("Invalid input date/time") from err

    @classmethod
    def __modify_schema__(cls, field_schema):
        """Make field JSON schema serializable."""
        field_schema.update(type="string", example="2023-01-01")


class IRI(str):
    """Pydantic custom data type validating RFC 3987 IRIs."""

    @classmethod
    def __get_validators__(cls):  # noqa: D105
        def validate(iri: str):
            """Checks whether the provided IRI is a valid RFC 3987 IRI."""
            rfc3987.parse(iri, rule="IRI")
            return cls(iri)

        yield validate
