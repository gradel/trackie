import datetime as dt
from trackie.work.logic import get_daily_stats


def test_get_daily_stats(single_work_unit):

    start_date = dt.date(2025, 1, 10)
    end_date = dt.date(2025, 1, 11)
    daily_stats = get_daily_stats(
        single_work_unit,
        start_date=start_date,
        minutes_per_day=1,
        end_date=end_date,
    )
    assert len(daily_stats) == 1
    day_stat = daily_stats[0]
    assert day_stat.minutes == 1
    assert day_stat.diff == 0
