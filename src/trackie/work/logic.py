from collections import defaultdict
from collections.abc import Generator, Sequence
import datetime as dt
from pathlib import Path
import re
from typing import cast

from trackie.ansi_colors import GREEN, RESET
from trackie.output import (
    output_stats_csv,
    output_work_units_csv,
    pretty_print_day_stats,
    pretty_print_week_stats,
    pretty_print_work_units,
)
from trackie.utils import (
    daterange,
    get_week_range,
    check_format,
    error,
    TrackieFormatException,
)
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
        end_date = dt.date.today()

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
        end_date = dt.date.today()

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
        end_date = dt.date.today()

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


def handle_command(params):
    lines = list(get_lines(params.data_path))

    try:
        check_format(
            lines,
            date_pattern=params.date_pattern,
            description_pattern=params.description_pattern,
            duration_pattern=params.duration_pattern,
        )
    except TrackieFormatException as e:
        error(f'{e.args[0]}')

    work_units = get_work_units(
        lines,
        params.client,
        start_date=params.start_date,
        date_pattern=params.date_pattern,
        description_pattern=params.description_pattern,
        duration_pattern=params.duration_pattern,
    )

    if params.mode == 'aggregate':
        if params.interval == 'week':
            params.minutes_per_week = cast(int, params.minutes_per_week)
            weekly_stats = get_weekly_stats(
                work_units,
                start_date=params.start_date,
                minutes_per_week=params.minutes_per_week,
                #  end_date=end_date,
            )
            if params.csv:
                output_path = output_stats_csv(weekly_stats, params)
                print(GREEN + f'Created CSV file at {output_path}' + RESET)
                return
            else:
                pretty_print_week_stats(weekly_stats, params)
                return

        elif params.interval == 'day':
            params.minutes_per_day = cast(int, params.minutes_per_day)
            daily_stats = get_daily_stats(
                work_units,
                start_date=params.start_date,
                minutes_per_day=params.minutes_per_day,
                #  end_date=end_date,
                excluded_weekdays=[5, 6],
            )
            if params.csv:
                output_path = output_stats_csv(daily_stats, params)
                print(GREEN + f'Created CSV file at {output_path}' + RESET)
            else:
                pretty_print_day_stats(daily_stats, params)

    elif params.mode == 'list':
        if params.csv:
            output_path = output_work_units_csv(work_units, params)
            print(GREEN + f'Created CSV file at {output_path}' + RESET)
        else:
            pretty_print_work_units(work_units, params)
