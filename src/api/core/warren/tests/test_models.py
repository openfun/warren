"""Tests for the core models."""

import datetime
from random import randint

import pytest

from warren.filters import DatetimeRange
from warren.models import DailyCount, DailyCounts, DailyUniqueCount, DailyUniqueCounts


def test_daily_count_add():
    """Test the `__add__` method from DailyCount model."""
    # Define four DailyCount, three sharing the same date
    count1 = DailyCount(date="2023-01-01", count=10)
    count2 = DailyCount(date="2023-01-02", count=1)
    count3 = DailyCount(date="2023-01-01", count=3)
    count4 = DailyCount(date="2023-01-01", count=6)

    # Sum DailyCount instances with the same date
    count5 = count1 + count3
    count6 = count1 + count3 + count4

    # New DailyCount should be the sum of the initial ones
    assert count5.count == count1.count + count3.count
    assert count6.count == count1.count + count3.count + count4.count

    # Ensure that the initial DailyCount instances remain unchanged
    assert count1.count == 10
    assert count3.count == 3
    assert count4.count == 6

    # Verify that attempting to add DailyCount instances with
    # different dates raises an exception
    msg = "Cannot add two DailyCount instances with different dates"
    with pytest.raises(ValueError, match=msg):
        count1 + count2

    # Verify that attempting to add a DailyCount instance and a
    # non-DailyCount value raises an exception
    msg = "'int' object has no attribute 'date'"
    with pytest.raises(AttributeError, match=msg):
        count1 + 10


def test_daily_counts_from_range():
    """Test the `from_range` class method from DailyCounts model."""
    date_range = DatetimeRange.parse_obj({"since": "2022-12-31", "until": "2023-01-30"})

    # Create DailyCounts from the date range
    daily_counts = DailyCounts.from_range(date_range.since, date_range.until)

    # Ensure there is one DailyCount per day, all initialized to zero
    assert len(daily_counts.counts) == 31
    assert daily_counts.total == 0

    # DailyCounts should be sorted by date and have a count of zero
    first_count = daily_counts.counts[0]
    assert first_count.date == datetime.date(2022, 12, 31)
    assert first_count.count == 0

    for idx, daily_count in enumerate(daily_counts.counts[1:]):
        assert daily_count.date == datetime.date(2023, 1, idx + 1)
        assert daily_count.count == 0


def test_daily_counts_merge_counts():
    """Test the `merge_counts` method from DailyCounts model."""
    # Create initial DailyCount objects
    count1 = DailyCount(date="2023-01-01", count=randint(0, 100))  # noqa: S311
    count2 = DailyCount(date="2023-01-02", count=randint(0, 100))  # noqa: S311

    # Create a DailyCounts object and merge counts
    count3 = DailyCounts(counts=[count1, count2], total=randint(0, 100))  # noqa: S311
    count3.merge_counts([count1, count1])

    # Verify that counts on 2023-01-01 have been summed
    assert count3.total == count1.count * 3 + count2.count
    assert count3.counts == [
        DailyCount(date=count1.date, count=count1.count * 3),
        count2,
    ]

    # Add a new count with a new date
    count4 = DailyCount(date="2023-01-03", count=randint(0, 100))  # noqa: S311
    count3.merge_counts([count4])

    # Ensure counts are sorted, and 2023-01-03 has been added at the end
    assert count3.total == count1.count * 3 + count2.count + count4.count
    assert count3.counts == [
        DailyCount(date=count1.date, count=count1.count * 3),
        count2,
        count4,
    ]

    # Merge several new counts with a new date
    count5 = DailyCount(date="2022-12-31", count=randint(0, 100))  # noqa: S311
    count3.merge_counts([count5, count5, count1])

    # Ensure counts are sorted, and 2022-12-31 has been added at the start
    assert (
        count3.total
        == count1.count * 4 + count2.count + count4.count + count5.count * 2
    )
    assert count3.counts == [
        DailyCount(date=count5.date, count=count5.count * 2),
        DailyCount(date=count1.date, count=count1.count * 4),
        count2,
        count4,
    ]


def test_daily_unique_count_add():
    """Test the `__add__` method from DailyUniqueCount model."""
    count1 = DailyUniqueCount(
        date="2023-01-01", count=3, users={"leia", "luke", "vader"}
    )
    count2 = DailyUniqueCount(date="2023-01-02", count=1, users={"luke"})
    count3 = DailyUniqueCount(date="2023-01-01", count=2, users={"luke", "han"})
    count4 = DailyUniqueCount(date="2023-01-01", count=0, users=set())

    # Sum instances with the same date
    count5 = count1 + count3
    count6 = count1 + count3 + count4

    assert count5.count == 4
    assert count5.users == {"leia", "luke", "vader", "han"}
    assert count6.count == 4
    assert count6.users == {"leia", "luke", "vader", "han"}

    # Verify that attempting to add DailyCount instances with
    # different dates raises an exception
    msg = "Cannot add two DailyUniqueCount instances with different dates"
    with pytest.raises(ValueError, match=msg):
        count1 + count2

    # Verify that attempting to add a DailyCount instance and a
    # non-DailyCount value raises an exception
    msg = "'int' object has no attribute 'date'"
    with pytest.raises(AttributeError, match=msg):
        count1 + 10


def test_daily_unique_count_to_daily_count():
    """Test the `to_daily_count` method from DailyUniqueCount model."""
    assert DailyUniqueCount(
        date="2023-01-01", count=3, users={"leia", "luke", "vader"}
    ).to_daily_count() == DailyCount(date="2023-01-01", count=3)


def test_daily_unique_counts_from_range():
    """Test the `from_range` class method from DailyUniqueCounts model."""
    date_range = DatetimeRange.parse_obj({"since": "2022-12-31", "until": "2023-01-30"})

    # Create DailyCounts from the date range
    daily_counts = DailyUniqueCounts.from_range(date_range.since, date_range.until)

    # Ensure there is one DailyCount per day, all initialized to zero
    assert len(daily_counts.counts) == 31
    assert daily_counts.total == 0

    # DailyCounts should be sorted by date and have a count of zero
    first_count = daily_counts.counts[0]
    assert first_count.date == datetime.date(2022, 12, 31)
    assert first_count.count == 0
    assert first_count.users == set()

    for idx, daily_count in enumerate(daily_counts.counts[1:]):
        assert daily_count.date == datetime.date(2023, 1, idx + 1)
        assert daily_count.count == 0
        assert daily_count.users == set()


def test_daily_unique_counts_merge_counts():
    """Test the `merge_counts` method from DailyUniqueCounts model."""
    count1 = DailyUniqueCount(
        date="2023-01-01", count=3, users={"leia", "luke", "vader"}
    )
    count2 = DailyUniqueCount(date="2023-01-02", count=1, users={"luke"})
    count3 = DailyUniqueCount(
        date="2023-01-03", count=4, users={"luke", "han", "vader", "yoda"}
    )

    # Create a DailyCounts object and merge counts
    counts = DailyUniqueCounts(
        counts=[count1],
        total=3,
    )
    counts.merge_counts([count2])

    # Verify that counts on 2023-01-01 have been summed
    assert counts.total == 3
    assert counts.counts == [
        DailyUniqueCount(date=count1.date, count=count1.count, users=count1.users),
        DailyUniqueCount(date=count2.date, count=0, users=set()),
    ]

    # Add a new count with a new date
    counts.merge_counts([count3])

    # Ensure counts are sorted, and 2023-01-03 has been added at the end
    assert counts.total == 5
    assert counts.counts == [
        DailyUniqueCount(date=count1.date, count=count1.count, users=count1.users),
        DailyUniqueCount(date=count2.date, count=0, users=set()),
        DailyUniqueCount(date=count3.date, count=2, users={"han", "yoda"}),
    ]

    # Merge several new counts with a new date
    count4 = DailyUniqueCount(date="2022-12-31", count=1, users={"han"})
    counts.merge_counts([count4])

    # Ensure counts are sorted, and 2022-12-31 has been added at the start
    assert counts.total == 5
    assert counts.counts == [
        count4,
        DailyUniqueCount(date=count1.date, count=count1.count, users=count1.users),
        DailyUniqueCount(date=count2.date, count=0, users=set()),
        DailyUniqueCount(date=count3.date, count=1, users={"yoda"}),
    ]


def test_daily_unique_counts_to_daily_count():
    """Test the `to_daily_count` method from DailyUniqueCounts model."""
    assert DailyUniqueCounts(
        total=8,
        counts=[
            DailyUniqueCount(
                date="2023-01-01", count=3, users={"leia", "luke", "vader"}
            ),
            DailyUniqueCount(date="2023-01-02", count=1, users={"luke"}),
            DailyUniqueCount(
                date="2023-01-03", count=4, users={"luke", "han", "vader", "yoda"}
            ),
        ],
    ).to_daily_counts() == DailyCounts(
        total=8,
        counts=[
            DailyCount(date="2023-01-01", count=3),
            DailyCount(date="2023-01-02", count=1),
            DailyCount(date="2023-01-03", count=4),
        ],
    )
