from collections import defaultdict
from collections.abc import Generator, Sequence
import datetime as dt
from pathlib import Path
from typing import Literal

from .conf import VIM_OTL_FILEPATH, MINUTES_PER_WEEK
from .models import WorkUnit


WORK_FILE = Path(VIM_OTL_FILEPATH)


def get_lines(path):
    with path.open() as f:
        lines = f.readlines()
        return lines


def get_work_units(
    lines: Sequence[str] | None = None,
    start_date: dt.date | None = None,
    end_date: dt.date | None = None,
) -> Generator[WorkUnit]:
    # date filter flag
    not_in_range = False

    if lines is None:
        lines = get_lines(WORK_FILE)

    for line in lines:
        if not line.strip():
            continue
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
            client = line.strip()
            continue
        if not_in_range is False:
            minutes = int(line.rsplit(':', 1)[1].strip())
            work_unit = WorkUnit(date, client, minutes)
            yield work_unit


def get_stats(
    start_date: dt.date | None = None,
    end_date: dt.date | None = None,
    group_by: Literal['day', 'week', 'month'] | None = 'week',
) -> None:
    work_units = list(get_work_units(start_date=start_date, end_date=end_date))
    work_units = sorted(work_units, key=lambda unit: unit.date)
    if group_by in [None, 'day']:
        work_per_day = defaultdict(int)
        for work_unit in work_units:
            work_per_day[work_unit.date] += work_unit.minutes
        return work_per_day

    elif group_by == 'week':
        if len(work_units) == 0:
            return {}

        if len(work_units) == 1:
            work_unit = work_units[0]
            day = work_unit.date
            week = day.isocalendar()[1]
            return {week: work_unit.minutes}

        work_per_week = defaultdict(int)
        for work_unit in work_units:
            day = work_unit.date
            week = day.isocalendar()[1]
            work_per_week[week] += work_unit.minutes
        annotated_work_per_week = {}
        for week, minutes in work_per_week.items():
            annotated_work_per_week[week] = (minutes, minutes - MINUTES_PER_WEEK)
        print(annotated_work_per_week)

        accumulated_work_per_week = {}
        running = 0
        for index, (week, minutes) in enumerate(work_per_week.items()):
            if index == 0:
                running = minutes - MINUTES_PER_WEEK
                accumulated_work_per_week[week] = (minutes, running)
            else:
                accumulated_work_per_week[week] = (minutes + running, running)
                running = minutes + running - MINUTES_PER_WEEK
        print(accumulated_work_per_week)
        return work_per_week
