"""Tests for the video indicators."""

import pandas as pd
import pytest
from dateutil.tz import tzoffset
from warren.factories.base import BaseXapiStatementFactory
from warren.filters import DatetimeRange
from warren.xapi import StatementsTransformer
from warren_video.indicators import BaseDailyEvent


@pytest.mark.anyio
async def test_base_daily_event_subclass_verb_id():
    """Test __init_subclass__ for the BaseDailyEvent class."""

    class MyIndicator(BaseDailyEvent):
        verb_id = "test"

    # the __init_subclass__ is called when the class itself is constructed.
    # It should raise an error because the 'verb_id' class attribute is missing.
    with pytest.raises(TypeError) as exception:

        class MyIndicatorMissingAttribute(BaseDailyEvent):
            wrong_attribute = "test"

    assert str(exception.value) == "Indicators must declare a 'verb_id' class attribute"


def test_base_daily_event_date_range_timezone():
    """Test 'to_date_range_timezone' for the BaseDailyEvent class."""
    # Create source statements
    raw_statements = [
        BaseXapiStatementFactory.build(
            mutations=[{"timestamp": "2023-01-01T00:10:00.000000+00:00"}]
        ).dict(),
        BaseXapiStatementFactory.build(
            mutations=[{"timestamp": "2023-01-03T00:10:00.000000+00:00"}]
        ).dict(),
    ]
    source_statements = StatementsTransformer.preprocess(raw_statements)

    # Create an indicator with a DateTimeRange in UTC
    indicator_utc = BaseDailyEvent(
        date_range=DatetimeRange(since="2023-01-01", until="2023-01-03"),
        video_id="Test",
        unique=True,
    )
    # Convert statements' timestamp
    statements = indicator_utc.to_date_range_timezone(source_statements)

    expected_statements = pd.to_datetime(
        pd.Series(
            [
                "2023-01-01T00:10:00+00:00",
                "2023-01-03T00:10:00+00:00",
            ],
            name="timestamp",
        )
    )

    # Statements' timestamp should be in UTC.
    assert statements["timestamp"].equals(expected_statements)

    # Create an indicator with a DateTimeRange in UTC+02:00
    indicator_with_timezone = BaseDailyEvent(
        date_range=DatetimeRange(
            since="2023-01-01T00:00:00+02:00", until="2023-01-03T00:00:00+02:00"
        ),
        video_id="Test",
        unique=True,
    )
    # Convert statements' timestamp
    statements = indicator_with_timezone.to_date_range_timezone(source_statements)

    # Statements' timestamp should be in UTC+02:00
    assert statements["timestamp"].equals(
        expected_statements.dt.tz_convert(tzoffset(None, 7200))
    )


def test_base_daily_event_add_date_column():
    """Test 'add_date_column' for the BaseDailyEvent class."""
    raw_statements = [
        BaseXapiStatementFactory.build(
            mutations=[{"timestamp": "2023-01-01T00:10:00.000000+00:00"}]
        ).dict(),
        BaseXapiStatementFactory.build(
            mutations=[{"timestamp": "2023-01-03T00:10:00.000000+00:00"}]
        ).dict(),
    ]
    source_statements = StatementsTransformer.preprocess(raw_statements)
    statements = BaseDailyEvent.extract_date_from_timestamp(source_statements)

    assert statements["date"].equals(
        pd.to_datetime(pd.Series(["2023-01-01", "2023-01-03"], name="date")).dt.date
    )
    assert "timestamp" not in statements.columns
