from collections import defaultdict
from collections.abc import Generator, Sequence
import datetime as dt
from pathlib import Path

from ..utils import daterange
from trackie.conf import get_config
from .models import WorkUnit, WeekStat, DayStat


def get_lines(path: Path) -> Generator[str]:
    with path.open() as f:
        lines = f.readlines()
        for line in lines:
            if line.strip():
                yield line


def get_work_units(
    lines: Generator[str],
    client: str,
    start_date: dt.date,
    end_date: dt.date | None = None,
) -> Generator[WorkUnit]:

    if not end_date:
        end_date = dt.date.today() + dt.timedelta(days=1)

    # date filter flag
    not_in_range = False

    for line in lines:
        if not line.startswith('\t'):
            date_str = line.strip()
            date = dt.datetime.strptime(date_str, "%Y-%m-%d").date()
            if (
                start_date and date < start_date
            ) or (
                end_date and date > end_date
            ):
                not_in_range = True
            else:
                not_in_range = False
            continue
        if line.startswith('\t') and not line.startswith('\t\t'):
            _client = line.strip()
            continue
        if not_in_range is False:
            minutes = int(line.rsplit(':', 1)[1].strip())
            work_unit = WorkUnit(date, client, minutes)
            if work_unit.client.lower() == client.lower():
                yield work_unit


def get_daily_stats(
    work_units: Generator[WorkUnit],
    start_date: dt.date,
    end_date: dt.date | None = None,
    excluded_weekdays: Sequence[int] | None = None,
) -> Sequence[DayStat]:

    config = get_config()

    if not end_date:
        end_date = dt.date.today() + dt.timedelta(days=1)

    # aggregate work on days
    work_per_day: dict[dt.date, int] = defaultdict(int)
    for work_unit in work_units:
        work_per_day[work_unit.date] += work_unit.minutes

    day_stats = []
    carryover = 0
    for date in daterange(start_date, end_date, excluded_weekdays=excluded_weekdays):
        minutes = work_per_day.get(date, 0)
        if date == start_date:
            diff = carryover = minutes - config.minutes_per_day
            day_stat = DayStat(date, minutes, diff, diff)
            day_stats.append(day_stat)
        else:
            carryover = minutes + carryover - config.minutes_per_day
            diff = minutes - config.minutes_per_day
            day_stat = DayStat(date, minutes, diff, carryover)
            day_stats.append(day_stat)
    return day_stats


def get_weekly_stats(
    work_units: Generator[WorkUnit],
    start_date: dt.date,
    end_date: dt.date | None = None,
) -> Sequence[WeekStat]:

    config = get_config()

    if not end_date:
        end_date = dt.date.today() + dt.timedelta(days=1)

    # aggregate work over weeks
    work_per_week: dict[tuple[int, int], int] = defaultdict(int)
    for work_unit in work_units:
        day = work_unit.date
        week = day.isocalendar()[1]
        work_per_week[(work_unit.date.year, week)] += work_unit.minutes

    week_stats = []
    carryover = 0
    for index, ((year, week), minutes) in enumerate(work_per_week.items()):
        if index == 0:
            diff = carryover = minutes - config.minutes_per_week
            week_stat = WeekStat(year, week, minutes, diff, diff)
            week_stats.append(week_stat)
        else:
            carryover = minutes + carryover - config.minutes_per_week
            diff = minutes - config.minutes_per_week
            week_stat = WeekStat(year, week, minutes, diff, carryover)
            week_stats.append(week_stat)
    return week_stats
