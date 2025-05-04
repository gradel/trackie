from collections import defaultdict
from collections.abc import Generator, Sequence
import datetime as dt
from typing import cast

from trackie.ansi_colors import GREEN, RESET
from trackie.output import (
    output_stats_csv,
    output_work_units_csv,
    pretty_print_day_stats,
    pretty_print_week_stats,
    pretty_print_work_units,
)
from trackie.repositories.base import WorkRepository
from trackie.utils import (
    daterange,
    get_week_range,
)
from .models import WorkUnit, WeekStat, DayStat


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


def handle_command(params, repository: WorkRepository):

    work_units = repository.get_work_units(params)

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
