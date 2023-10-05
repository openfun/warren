"""Tests for the video indicators."""

import pytest
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
