"""Warren model fields."""

import rfc3987


class IRI(str):
    """Pydantic custom data type validating RFC 3987 IRIs."""

    @classmethod
    def __get_validators__(cls):  # noqa: D105
        def validate(iri: str):
            """Checks whether the provided IRI is a valid RFC 3987 IRI."""
            rfc3987.parse(iri, rule="IRI")
            return cls(iri)

        yield validate
