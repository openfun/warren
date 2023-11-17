"""Warren API filters."""

import arrow
from fastapi import HTTPException, status
from pydantic import BaseModel, ValidationError, root_validator

from .conf import settings
from .fields import Datetime


class DatetimeRange(BaseModel):
    """A date/time range."""

    since: Datetime
    until: Datetime

    class Config:
        """Datetime range model configuration."""

        arbitrary_types_allowed = True
        validate_assignment = True

    @root_validator(pre=True)
    @classmethod
    def set_datetime_range_defaults(cls, values):
        """Set date/time range defaults to the last DEFAULT_DATETIMERANGE_SPAN days."""
        since, until = map(values.get, ["since", "until"])

        if since is None and until is None:
            until = arrow.utcnow()
            since = until - settings.DEFAULT_DATETIMERANGE_SPAN

        elif until is None:
            since = Datetime.validate(since)
            until = arrow.now(since.tzinfo)

        elif since is None:
            until = Datetime.validate(until)
            since = until - settings.DEFAULT_DATETIMERANGE_SPAN

        values.update(
            {
                "since": since,
                "until": until,
            }
        )
        return values

    @root_validator
    @classmethod
    def check_range_consistency(cls, values):
        """Check date/time range consistency."""
        if values.get("since") > values.get("until"):
            raise ValueError("Invalid date range: since cannot be after until")
        if values.get("since").tzinfo != values.get("until").tzinfo:
            raise ValueError(
                "Invalid date range: since and until cannot have different timezones"
            )
        return values

    @property
    def tzinfo(self):
        """Return the shared timezone information of the date range."""
        return self.since.tzinfo


class BaseQueryFilters(DatetimeRange):
    """Common query filters that every API endpoint should implement."""

    @root_validator
    @classmethod
    def check_datetime_range_consistency(cls, values):
        """Check date/time range consistency.

        A wrapper for the DatetimeRange.check_range_consistency root validator
        that raises an HTTPException instead of a ValueError since FastAPI does
        not support root validators for query models dependency injections.

        See: https://github.com/tiangolo/fastapi/discussions/9071

        """
        try:
            DatetimeRange.parse_obj(values)
        except ValidationError as err:
            for error in err.errors():
                error["loc"] = ["query"] + list(error["loc"])
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY, detail=err.errors()
            ) from err
        return values

    @root_validator
    @classmethod
    def check_datetime_range_span(cls, values):
        """Check that date/time range is not too greedy."""
        since, until = map(values.get, ["since", "until"])
        if since + settings.MAX_DATETIMERANGE_SPAN < until:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Date/time range is too greedy.",
            )
        return values
