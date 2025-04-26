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
    output_work_units_csv,
    pretty_print_day_stats,
    pretty_print_week_stats,
    pretty_print_work_units,
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


def error(message):
    sys.exit(RED + BACKGROUND_BRIGHT_YELLOW + message + RESET)


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
    mode: Annotated[str | None, typer.Option(
        help=(
            "List work units or aggregate over interval. Possible values: "
            "list | aggregate"
        )
    )] = None,
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
):
    """
    Aggregate, display and export work time statistics.
    """

    config = get_config()

    if not mode:
        mode = config.mode

    if start is None:
        start_date = config.start_date
        if start_date is None:
            today = dt.date.today()
            start_date = dt.date(year=today.year, month=today.month, day=1)
    else:
        try:
            start_date = dt.datetime.strptime(start, '%Y-%m-%d').date()
        except ValueError:
            error(
                f'Format of start date is invalid: {start}. '
                'Must match YYYY-MM-DD'
            )

    if client in config.abbr:
        client = config.abbr[client]

    if client is None:
        client = config.default
        if client is None:
            error(
                'No default client is set in the config file, '
                'Provide one as argument or set one in the config file'
            )
    try:
        data_path = Path(config.clients[client])
    except KeyError:
        error(
            f'Error: Client "{client}" not found in "clients" table '
            'in YAML config file.'
        )

    if not data_path.exists():
        error(f'Error: File "{data_path}" does not exist.')

    lines = list(get_lines(data_path))

    try:
        check_format(lines, config)
    except TrackieFormatException as e:
        error(f'{e.args[0]}')

    work_units = get_work_units(
        lines, client, config, start_date=start_date)

    if mode == 'aggregate':
        if interval == 'week':
            if not config.minutes_per_week:
                error(
                    '"minutes_per_week" config value must be set in'
                    ' config file when using interval "week"'
                )
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
                return
            else:
                pretty_print_week_stats(
                    client, weekly_stats, config.minutes_per_week)
                return

        elif interval == 'day':
            if not config.minutes_per_day:
                error(
                    '"minutes_per_day" config value must be set in'
                    ' config file when using interval "day"'
                )
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

    elif mode == 'list':
        work_units = get_work_units(lines, client, config, start_date)
        if not config.hourly_wages or client not in config.hourly_wages:
            error(
                f'Please provide a hourly wage value for "{client}" in '
                ' the config file when using "list" mode'
            )
        hourly_wage = config.hourly_wages[client]
        if csv:
            output_path = output_work_units_csv(
                work_units, client=client, hourly_wage=hourly_wage)
            print(GREEN + f'Created CSV file at {output_path}' + RESET)
        else:
            pretty_print_work_units(
                work_units, client=client, hourly_wage=hourly_wage
            )


if __name__ == '__main__':
    app()
