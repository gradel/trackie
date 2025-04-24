import datetime as dt
from pathlib import Path
import sys
from typing_extensions import Annotated

import typer

from trackie.ansi_colors import GREEN, RED, RESET, BACKGROUND_BRIGHT_YELLOW
from trackie.conf import get_config
from trackie.output import (
    output_day_stats_csv,
    output_week_stats_csv,
    pretty_print_day_stats,
    pretty_print_week_stats,
)
from trackie.utils import (
    check_format,
    TrackieFormatException,
)
from trackie.work.stats import (
    get_daily_stats,
    get_weekly_stats,
    get_lines,
    get_work_units,
)


app = typer.Typer()


def get_default_client() -> str | None:
    config = get_config()
    if config.default and 'client' in config.default:
        return config.default['client']
    return None


@app.command()
def run(
    client: Annotated[str, typer.Argument(
        default_factory=get_default_client,
        help="May be omitted if a default client is set in config file")],
    start: Annotated[str | None, typer.Option(
        help=(
            "Use data after this date. Format: YYYY-MM-DD. "
            "Default: from start of current month or start_date "
            "in config file if set"
        ))] = None,
    interval: Annotated[str, typer.Option(
        help=(
            "Show data aggregated per day or per week. Possible values: "
            "day|week"
        )
    )] = 'week',
    csv: Annotated[bool, typer.Option(
        help=(
            "Export data to CSV file in your home directory. The file's name "
            "will contain the client's name and the current time"
        ))] = False,
    # config_path: str | None = None,
):
    """
    Aggregate, display and export work time statistics.
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

    if client is None:
        sys.exit(
            RED + BACKGROUND_BRIGHT_YELLOW + 'No default client is set in '
            'the config file, so you have to provide one as argument.' + RESET
        )
    try:
        data_path = config.clients[client]
    except KeyError:
        sys.exit(
            RED + f'Error: Client "{client}" not found in "clients" '
            'table in YAML config file.' + RESET
        )

    lines = list(get_lines(Path(data_path)))

    try:
        check_format(lines)
    except TrackieFormatException as e:
        print(RED + BACKGROUND_BRIGHT_YELLOW + f'{e.args[0]}' + RESET)
        sys.exit(-1)

    work_units = get_work_units(
        lines, client, config, start_date=start_date)

    if interval == 'week':
        if not config.minutes_per_week:
            sys.exit(
                RED + BACKGROUND_BRIGHT_YELLOW
                + '"minutes_per_week" config value must be set in'
                + ' ~/.trackie.toml when using interval "week"' + RESET)
        weekly_stats = get_weekly_stats(
            work_units,
            start_date=start_date,
            minutes_per_week=config.minutes_per_week,
            #  end_date=end_date,
        )
        if csv:
            output_path = output_week_stats_csv(
                client, weekly_stats, config.minutes_per_week)
            print(GREEN + f'Created CSV file at {output_path}' + RESET)
        else:
            pretty_print_week_stats(
                client, weekly_stats, config.minutes_per_week)

    elif interval == 'day':
        if not config.minutes_per_day:
            sys.exit(
                RED + BACKGROUND_BRIGHT_YELLOW
                + '"minutes_per_day" config value must be set in'
                + ' ~/.trackie.toml when using interval "day"' + RESET)
        daily_stats = get_daily_stats(
            work_units,
            start_date=start_date,
            minutes_per_day=config.minutes_per_day,
            #  end_date=end_date,
            excluded_weekdays=[5, 6],
        )
        if csv:
            output_path = output_day_stats_csv(
                client, daily_stats, config.minutes_per_day)
            print(GREEN + f'Created CSV file at {output_path}' + RESET)
        else:
            pretty_print_day_stats(
                client, daily_stats, config.minutes_per_day)


if __name__ == '__main__':
    app()
