from collections import defaultdict
from collections.abc import Generator, Sequence
import datetime as dt
from pathlib import Path
import re

from trackie.utils import daterange, get_week_range
from .models import WorkUnit, WeekStat, DayStat


def get_lines(
    path: Path,
) -> Generator[str]:
    with path.open() as f:
        for line in f:
            if line.strip():
                yield line


def get_work_units(
    lines: Sequence[str],
    client: str,
    *,
    start_date: dt.date,
    date_pattern: re.Pattern,
    description_pattern: re.Pattern,
    duration_pattern: re.Pattern,
    end_date: dt.date | None = None,
) -> Generator[WorkUnit]:

    if not end_date:
        end_date = dt.date.today() + dt.timedelta(days=1)

    # date filter flag
    not_in_range = False
    description = ''

    for line in lines:
        if date_pattern.match(line):
            date_str = line.strip()
            date = dt.datetime.strptime(date_str, "%Y-%m-%d").date()
            not_in_range = True if date < start_date or date > end_date else False  # noqa: W501
            continue
        elif description_pattern.match(line) and not_in_range is False:
            description += f' {line.strip()}'
            continue
        elif duration_pattern.match(line) and not_in_range is False:
            minutes = int(line.strip())
            work_unit = WorkUnit(date, client, minutes, description)
            description = ''
            if work_unit.client.lower() == client.lower():
                yield work_unit


def get_daily_stats(
    work_units: Generator[WorkUnit],
    *,
    start_date: dt.date,
    minutes_per_day: int,
    end_date: dt.date | None = None,
    excluded_weekdays: Sequence[int] | None = None,
) -> Sequence[DayStat]:

    if not end_date:
        end_date = dt.date.today() + dt.timedelta(days=1)

    # aggregate work on days
    work_per_day: dict[dt.date, int] = defaultdict(int)
    for work_unit in work_units:
        work_per_day[work_unit.date] += work_unit.minutes

    day_stats = []
    carryover = 0
    for date in daterange(
            start_date, end_date, excluded_weekdays=excluded_weekdays):
        minutes = work_per_day.get(date, 0)
        if date == start_date:
            diff = carryover = minutes - minutes_per_day
            day_stat = DayStat(date, minutes, diff, diff)
            day_stats.append(day_stat)
        else:
            carryover = minutes + carryover - minutes_per_day
            diff = minutes - minutes_per_day
            day_stat = DayStat(date, minutes, diff, carryover)
            day_stats.append(day_stat)
    return day_stats


def get_weekly_stats(
    work_units: Generator[WorkUnit],
    *,
    start_date: dt.date,
    minutes_per_week: int,
    end_date: dt.date | None = None,
) -> Sequence[WeekStat]:

    if not end_date:
        end_date = dt.date.today() + dt.timedelta(days=1)

    weeks_to_report = get_week_range(start_date, end_date)

    # aggregate work over weeks
    work_per_week: dict[tuple[int, int], int] = defaultdict(int)
    for work_unit in work_units:
        day = work_unit.date
        week = day.isocalendar()[1]
        work_per_week[(work_unit.date.year, week)] += work_unit.minutes

    year = start_date.year
    weeks = [year_and_week[1] for year_and_week in work_per_week.keys()]
    for week in weeks_to_report:
        if week not in weeks:
            work_per_week[(year, week)] = 0

    week_stats = []
    carryover = 0
    for index, ((year, week), minutes) in enumerate(work_per_week.items()):
        if index == 0:
            diff = carryover = minutes - minutes_per_week
            week_stat = WeekStat(year, week, minutes, diff, diff)
            week_stats.append(week_stat)
        else:
            carryover = minutes + carryover - minutes_per_week
            diff = minutes - minutes_per_week
            week_stat = WeekStat(year, week, minutes, diff, carryover)
            week_stats.append(week_stat)
    return sorted(week_stats, key=lambda week_stat: week_stat.week)
