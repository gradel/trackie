import datetime as dt
from pathlib import Path

import typer

from trackie.work.stats import (
    get_daily_stats,
    get_weekly_stats,
    get_lines,
    get_work_units,
)
from trackie.utils import pretty_print_day_stats, pretty_print_week_stats
from trackie.conf import get_config


def run(
    client: str,
    start: str | None = None,
    interval: str | None = 'week',
):
    """
    Display work time statistics.
    """

    config = get_config()

    if start is None:
        start_date = config.start_date
        if start_date is None:
            today = dt.date.today()
            start_date = dt.date(year=today.year, month=today.month, day=1)
    else:
        start_date = dt.datetime.strptime(start, '%Y-%m-%d').date()

    if client in config.abbr:
        client = config.abbr[client]

    try:
        vim_otl_filepath = config.clients[client]
    except KeyError:
        import sys
        sys.exit(
            f'Error: Client {client} not found in "clients" '
            'table in YAML config file!'
        )

    lines = get_lines(Path(vim_otl_filepath))
    work_units = get_work_units(lines, client, start_date=start_date)

    if interval == 'week':
        weekly_stats = get_weekly_stats(
            work_units=work_units,
            start_date=start_date,
            #  end_date=end_date,
        )
        pretty_print_week_stats(client, weekly_stats, config.minutes_per_week)

    elif interval == 'day':
        daily_stats = get_daily_stats(
            work_units=work_units,
            start_date=start_date,
            #  end_date=end_date,
            excluded_weekdays=[5, 6]
        )
        pretty_print_day_stats(client, daily_stats, config.minutes_per_day)


def main():
    typer.run(run)
