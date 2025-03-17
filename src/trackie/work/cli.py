import datetime as dt
from pathlib import Path

from trackie.work.stats import (
    get_daily_stats,
    get_weekly_stats,
    get_lines,
    get_work_units,
)
from trackie.utils import print_pretty_day_stats, print_pretty_week_stats
from trackie.conf import get_config


def main():
    config = get_config()

    start_date = dt.date(2025, 3, 3)

    lines = get_lines(Path(config.vim_otl_filepath))
    work_units = get_work_units(lines, start_date=start_date)

    weekly_stats = get_weekly_stats(
       work_units=work_units,
       start_date=start_date,
       #  end_date=end_date,
    )
    #  print('Weekly Stats: ', weekly_stats)
    print_pretty_week_stats(weekly_stats, config.minutes_per_week)

    lines = get_lines(Path(config.vim_otl_filepath))
    work_units = get_work_units(lines, start_date=start_date)
    #  print(list(work_units))

    daily_stats = get_daily_stats(
        work_units=work_units,
        start_date=start_date,
        #  end_date=end_date,
        excluded_weekdays=[5, 6]
    )
    #  print('Daily Stats: ', daily_stats)
    print_pretty_day_stats(daily_stats, config.minutes_per_day)
