"""Tests for the core API filters."""

import datetime

import arrow
import pytest
from dateutil.tz import tzoffset, tzutc
from fastapi import HTTPException
from freezegun import freeze_time
from pydantic import ValidationError

from warren.conf import settings
from warren.filters import BaseQueryFilters, DatetimeRange


# pylint: disable=no-member
def test_datetime_range_model():
    """Test the DatetimeRange model."""
    # Arrow supports various input string formats, let's just test one
    period = DatetimeRange(since="2023-01-01 10:42", until="2023-01-02 12:22")

    assert period.since.year == period.until.year == 2023
    assert period.since.month == period.until.month == 1
    assert period.since.day == 1
    assert period.since.hour == 10
    assert period.since.minute == 42
    assert period.until.day == 2
    assert period.until.hour == 12
    assert period.until.minute == 22

    # It also supports Arrow instances
    period = DatetimeRange(since=arrow.get("2023-01-01"), until=arrow.get("2023-01-02"))
    assert period.since.year == period.until.year == 2023
    assert period.since.month == period.until.month == 1
    assert period.since.day == 1
    assert period.until.day == 2
    assert period.since.hour == period.until.hour == 0
    assert period.since.minute == period.until.minute == 0

    with pytest.raises(
        ValidationError,
        match="since\\n  Invalid input date\\/time \\(type=value_error\\)",
    ):
        DatetimeRange(since="2023-01-ee", until="2023-01-01")

    with pytest.raises(
        ValidationError, match="Invalid date range: since cannot be after until"
    ):
        DatetimeRange(since="2023-01-02", until="2023-01-01")

    with pytest.raises(
        ValidationError,
        match="Invalid date range: since and until cannot have different timezones",
    ):
        DatetimeRange(
            since="2023-01-01T00:00:00+02:00", until="2023-01-03T22:00:00+04:00"
        )

    with pytest.raises(
        ValidationError,
        match="Invalid date range: since and until cannot have different timezones",
    ):
        period.since = arrow.get("2023-01-01T00:00:00+04:00")


# pylint: disable=no-member
def test_datetime_range_model_defaults(monkeypatch):
    """Test the DatetimeRange model defaults."""
    utcnow = arrow.utcnow()
    monkeypatch.setattr(arrow, "utcnow", lambda: utcnow)

    # Since and until fields are not required. We should not raise exceptions
    # if not all fields are provided.
    period = DatetimeRange()
    assert period.since == utcnow.shift(days=-7)
    assert period.until == utcnow

    with freeze_time("2023-01-14T12:00:00+02:00"):
        now = arrow.now(tz="Europe/Paris")
        period = DatetimeRange(since=now.shift(months=-6))
        assert period.until.tzinfo == now.tzinfo
        assert period.until == now

    period = DatetimeRange(until="2023.01.02")
    assert period.since == period.until - datetime.timedelta(days=7)


def test_datetime_range_tzinfo():
    """Test the DatetimeRange tzinfo property."""
    period_utc = DatetimeRange(
        since=arrow.get("2023-01-01"), until=arrow.get("2023-01-02")
    )
    assert period_utc.tzinfo == tzutc()

    period_default = DatetimeRange()
    assert period_default.tzinfo == tzutc()

    period_timezone = DatetimeRange(
        since=arrow.get("2023-01-01T00:00:00+02:00"),
        until=arrow.get("2023-01-02T00:00:00+02:00"),
    )
    # 7200 seconds is equal to 2 hours
    assert period_timezone.tzinfo == tzoffset(None, 7200)


def test_base_query_filters_model():
    """Test the BaseQueryFilters model."""
    filters = BaseQueryFilters(since="2023-01-11", until="2023-02-11")
    assert filters.since == arrow.get("2023-01-11")
    assert filters.until == arrow.get("2023-02-11")

    # Date/time range consistency
    with pytest.raises(HTTPException, match="422"):
        BaseQueryFilters(since="2023-01-11", until="2023-01-10")

    with pytest.raises(HTTPException, match="422"):
        BaseQueryFilters(
            since="2023-01-01T00:00:00+02:00", until="2023-01-03T22:00:00+04:00"
        )

    # Check Date/time range max span
    now = arrow.utcnow()
    since = now
    until = now + settings.MAX_DATETIMERANGE_SPAN
    filters = BaseQueryFilters(since=since, until=until)
    with pytest.raises(HTTPException, match="422"):
        BaseQueryFilters(since=since, until=until.shift(days=1))
