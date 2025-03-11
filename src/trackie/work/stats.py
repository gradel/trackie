from collections import defaultdict
import datetime as dt
from pathlib import Path

from .conf import VIM_OTL_FILEPATH
from .models import WorkUnit


WORK_FILE = Path(VIM_OTL_FILEPATH)


def get_lines(path):
    with path.open() as f:
        lines = f.readlines()
        return lines


def get_work_units():
    lines = get_lines(WORK_FILE)
    for line in lines:
        if not line.strip():
            continue
        if not line.startswith('\t'):
            date_str = line.strip()
            date = dt.datetime.strptime(date_str, "%Y-%m-%d").date()
            continue
        if line.startswith('\t') and not line.startswith('\t\t'):
            client = line.strip()
            continue
        minutes = int(line.rsplit(':', 1)[1].strip())
        work_unit = WorkUnit(date, client, minutes)
        yield work_unit


def get_stats():
    work_units = list(get_work_units())
    sorted_work_units = sorted(work_units, key=lambda unit: unit.date)
    print(sorted_work_units)
    work_per_day = defaultdict(int)
    for work_unit in work_units:
        work_per_day[work_unit.date] += work_unit.minutes
    print(work_per_day)
