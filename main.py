import datetime as dt
from pathlib import Path

from src.trackie.work.stats import (
    get_daily_stats,
    get_weekly_stats,
    get_lines,
    get_work_units,
)
from src.trackie.utils import print_pretty_day_stats, print_pretty_week_stats
from src.trackie.work.conf import (
    MINUTES_PER_DAY,
    MINUTES_PER_WEEK,
    VIM_OTL_FILEPATH,
)


if __name__ == "__main__":
    start_date = dt.date(2025, 3, 3)
    #  end_date = dt.date(2025, 3, 4)

    lines = get_lines(Path(VIM_OTL_FILEPATH))
    work_units = get_work_units(lines, start_date=start_date)

    weekly_stats = get_weekly_stats(
       work_units=work_units,
       start_date=start_date,
       #  end_date=end_date,
    )
    #  print('Weekly Stats: ', weekly_stats)
    print_pretty_week_stats(weekly_stats, MINUTES_PER_WEEK)

    lines = get_lines(Path(VIM_OTL_FILEPATH))
    work_units = get_work_units(lines, start_date=start_date)
    #  print(list(work_units))

    daily_stats = get_daily_stats(
        work_units=work_units,
        start_date=start_date,
        #  end_date=end_date,
        excluded_weekdays=[5, 6]
    )
    #  print('Daily Stats: ', daily_stats)
    print_pretty_day_stats(daily_stats, MINUTES_PER_DAY)
