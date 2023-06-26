"""Tests for pydantic model fields."""

import datetime
from typing import Any

import arrow
import pytest
from pydantic import BaseModel

from warren.fields import Date, Datetime


@pytest.mark.parametrize(
    "date",
    ["2023-12-01", "20231201", arrow.get("2023-12-01"), datetime.date(2023, 12, 1)],
)
def test_date_field(date: Any):
    """Test the Date warren field."""

    # pylint: disable=missing-class-docstring
    class MyModel(BaseModel):
        saved_at: Date

    my_model = MyModel(saved_at=date)  # type: ignore[arg-type]
    assert my_model.saved_at.year == 2023
    assert my_model.saved_at.month == 12
    assert my_model.saved_at.day == 1


def test_date_field_with_invalid_inputs() -> None:
    """Test the Date warren field with invalud inputs."""

    # pylint: disable=missing-class-docstring
    class MyModel(BaseModel):
        saved_at: Date

    with pytest.raises(ValueError, match="Invalid input date"):
        MyModel(saved_at="foo")  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "date_time",
    ["2023-12-01", "20231201", arrow.get("2023-12-01"), datetime.datetime(2023, 12, 1)],
)
def test_datetime_field(date_time: str):
    """Test the Datetime warren field."""

    # pylint: disable=missing-class-docstring
    class MyModel(BaseModel):
        saved_at: Datetime

    my_model = MyModel(saved_at=date_time)  # type: ignore[arg-type]
    assert my_model.saved_at.year == 2023
    assert my_model.saved_at.month == 12
    assert my_model.saved_at.day == 1


def test_datetime_field_with_invalid_inputs() -> None:
    """Test  the Datetime warren field with invalud inputs."""

    # pylint: disable=missing-class-docstring
    class MyModel(BaseModel):
        saved_at: Datetime

    with pytest.raises(ValueError, match="Invalid input date/time"):
        MyModel(saved_at="foo")  # type: ignore[arg-type]
