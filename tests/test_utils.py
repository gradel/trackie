import datetime as dt

from trackie.utils import get_week_range


def test_get_week_range_from_friday_to_monday_inclusive():
    start_date = dt.date(year=2025, month=3, day=7)
    assert start_date.isoweekday() == 5  # Friday

    end_date = dt.date(year=2025, month=3, day=17)
    assert end_date.isoweekday() == 1  # Monday

    weeks = get_week_range(start_date, end_date)
    assert list(weeks) == [10, 11, 12]
