import datetime as dt

from trackie.work.stats import get_work_units, get_daily_stats


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


def test_empty_file():
    lines = []
    assert list(get_work_units(
        lines, 'client', start_date=dt.date(2000, 1, 1))) == []


def test_one_work_unit():
    lines = [
        '2025-03-01',
        '\tTask 1',
        '\t\t5',
    ]
    work_units = list(get_work_units(
        lines, 'client', start_date=dt.date(2025, 3, 1)))
    assert len(work_units) == 1
    work_unit = work_units[0]
    assert work_unit.date.year == 2025
    assert work_unit.date.month == 3
    assert work_unit.date.day == 1


def test_four_days_exclude_outer():
    first_date = dt.date(2025, 3, 1)
    day_after_first_date = first_date + dt.timedelta(days=1)
    last_date = dt.date(2025, 3, 15)
    day_before_last_date = last_date - dt.timedelta(days=1)
    lines = [
        first_date.strftime('%Y-%m-%d'),
        '\tTask 1',
        '\t\t5',
        '2025-03-05',
        '\tTask 2',
        '\t\t10',
        '2025-03-10',
        '\tTask 3',
        '\t\t20',
        last_date.strftime('%Y-%m-%d'),
        '\tTask 4',
        '\t\t30',
    ]
    work_units = list(get_work_units(
        lines,
        'client',
        start_date=day_after_first_date,
        end_date=day_before_last_date
    ))
    assert len(work_units) == 2
    first_work_unit, second_work_unit = work_units
    assert first_work_unit.date.day == 5
    assert second_work_unit.date.day == 10
