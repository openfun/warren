"""Warren API filters."""

import arrow
from fastapi import HTTPException
from pydantic import BaseModel, ValidationError, model_validator

from .conf import settings
from .fields import Datetime


class DatetimeRange(BaseModel):
    """A date/time range."""

    since: Datetime = None
    until: Datetime = None

    class Config:
        """Datetime range model configuration."""

        arbitrary_types_allowed = True

    @model_validator(mode="before")
    @classmethod
    def set_datetime_range_defaults(cls, values):
        """Set date/time range defaults to the last DEFAULT_DATETIMERANGE_SPAN days."""
        now = arrow.utcnow()
        since, until = map(values.get, ["since", "until"])
        if until is None:
            until = Datetime.validate(now)
        else:
            until = Datetime.validate(until)
        values["until"] = until
        if since is None:
            values["since"] = Datetime.validate(
                until - settings.DEFAULT_DATETIMERANGE_SPAN
            )
        return values

    @model_validator(mode="after")
    @classmethod
    def check_range_consistency(cls, values):
        """Check date/time range consistency."""
        if values.get("since") > values.get("until"):
            raise ValueError("Invalid date range: since cannot be after until")
        return values


class BaseQueryFilters(DatetimeRange):
    """Common query filters that every API endpoint should implement."""

    @model_validator(mode="after")
    @classmethod
    def check_datetime_range_consistency(cls, values):
        """Check date/time range consistency.

        A wrapper for the DatetimeRange.check_range_consistency root validator
        that raises an HTTPException instead of a ValueError since FastAPI does
        not support root validators for query models dependency injections.

        See: https://github.com/tiangolo/fastapi/discussions/9071

        """
        try:
            DatetimeRange.model_validate(values)
        except ValidationError as err:
            for error in err.errors():
                error["loc"] = ["query"] + list(error["loc"])
            raise HTTPException(422, detail=err.errors()) from err
        return values

    @model_validator(mode="after")
    @classmethod
    def check_datetime_range_span(cls, values):
        """Check that date/time range is not too greedy."""
        since, until = map(values.get, ["since", "until"])
        if since + settings.MAX_DATETIMERANGE_SPAN < until:
            raise HTTPException(422, detail="Date/time range is too greedy.")
        return values
