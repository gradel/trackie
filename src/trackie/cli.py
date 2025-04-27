from dataclasses import dataclass
import datetime as dt
from decimal import Decimal
from pathlib import Path
import re
import sys
from typing import cast, Literal
from typing_extensions import Annotated

import typer

from trackie.ansi_colors import GREEN, RED, RESET, BACKGROUND_BRIGHT_YELLOW
from trackie.conf import get_config, Config
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

date_pattern = re.compile(r'''
    ^20[23]\d-  # year
    (01|02|03|04|05|06|07|08|09|10|11|12)-     # month
    (01|02|03|04|05|06|07|08|09|10|11|12|13|14|15|16|17|18|19|20|21|22|23|24|25|26|27|28|29|30|31)$   # day  # noqa: W501
''', re.VERBOSE)

tabs_description_pattern = re.compile(r'^\t[^\t].*')
tabs_duration_pattern = re.compile(r'^\t\t\d+')

spaces_description_pattern = r'^{}[^ ].*'
spaces_duration_pattern = r'^{}\d+'

app = typer.Typer()


def error(message):
    sys.exit(RED + BACKGROUND_BRIGHT_YELLOW + message + RESET)


@dataclass
class Params:
    client: str
    data_path: Path
    mode: Literal['list', 'aggregate']
    start_date: dt.date
    interval: Literal['day', 'week']
    csv: bool
    date_pattern: re.Pattern
    description_pattern: re.Pattern
    duration_pattern: re.Pattern
    minutes_per_day: int | None
    minutes_per_week: int | None
    hourly_wages: dict[str, Decimal]


def evaluate_input(
    *,
    client: str | None,
    mode: str | None,
    start: str | None,
    interval: str | None,
    csv: bool,
    config: Config,
) -> Params:
    """
    Validate and check cli args and config values.

    Return a dataclass with all needed values after sorting out
    all possible inconsistencies and dependencies.
    """
    if config.abbr and client in config.abbr:
        client = config.abbr[client]

    # `client` is the only value that gets already handled with a
    # default_factory for the argument in typer
    if not client:
        error(
            'No default client is set in the config file, '
            'Provide one as argument or set one in the config file'
        )

    if config.clients and client:
        try:
            data_path = Path(config.clients[client])
        except KeyError:
            error(
                f'Error: Client "{client}" not found in "clients" table '
                'in YAML config file.'
            )

    if not data_path.exists():
        error(f'Error: File "{data_path}" does not exist.')

    mode = mode or config.mode or 'list'

    hourly_wages = dict()
    if config.hourly_wages:
        # do not use and thereby change already defined variable client here!
        for _client, wage in config.hourly_wages.items():
            hourly_wages[_client] = Decimal(wage)

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

    if config.spaces:
        description_pattern = re.compile(
            spaces_description_pattern.format(' ' * config.spaces))
        duration_pattern = re.compile(
            spaces_duration_pattern.format(' ' * config.spaces * 2))
    else:
        description_pattern = tabs_description_pattern
        duration_pattern = tabs_duration_pattern

    interval = interval or config.interval

    if (
        mode == 'aggregate'
        and interval == 'week'
        and not config.minutes_per_week
    ):
        error(
            '"minutes_per_week" config value must be set in'
            ' config file when using interval "week"'
        )

    if (
        mode == 'aggregate'
        and interval == 'day'
        and not config.minutes_per_day
    ):
        error(
            '"minutes_per_day" config value must be set in'
            ' config file when using interval "day"'
        )

    if (
        mode == 'list'
        and (
            not config.hourly_wages
            or client not in config.hourly_wages
        )
    ):
        error(
            f'Please provide a hourly wage value for "{client}" in '
            ' the config file when using "list" mode'
        )

    client = cast(str, client)  # just for mypy, params.client has type str
    mode = cast(Literal['list', 'aggregate'], mode)
    interval = cast(Literal['day', 'week'], interval)
    start_date = cast(dt.date, start_date)

    params = Params(
        client=client,
        data_path=data_path,
        mode=mode,
        start_date=start_date,
        interval=interval,
        csv=csv,
        date_pattern=date_pattern,
        description_pattern=description_pattern,
        duration_pattern=duration_pattern,
        minutes_per_day=config.minutes_per_day,
        minutes_per_week=config.minutes_per_week,
        hourly_wages=hourly_wages,
    )
    return params


def get_default_client() -> str | None:
    config = get_config()
    if config.default and 'client' in config.default:
        return config.default['client']
    if not config.default and len(config.clients.keys()) == 1:
        return list(config.clients.keys())[0]
    return None


@app.command()
def run(
    client: Annotated[str, typer.Argument(
        default_factory=get_default_client,
        help=(
            "May be omitted if a default client is set in config file"
            " or there is only one client in config's clients table"
        )
    )],
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
    interval: Annotated[str | None, typer.Option(
        help=(
            "Show data aggregated per day or per week. Possible values: "
            "day|week"
        )
    )] = None,
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

    params = evaluate_input(
        client=client,
        mode=mode,
        start=start,
        interval=interval,
        csv=csv,
        config=config,
    )

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
                output_path = output_week_stats_csv(
                    params.client, weekly_stats, params.minutes_per_week)
                print(GREEN + f'Created CSV file at {output_path}' + RESET)
                return
            else:
                pretty_print_week_stats(
                    params.client, weekly_stats, params.minutes_per_week)
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
            if csv:
                output_path = output_day_stats_csv(
                    params.client, daily_stats, params.minutes_per_day)
                print(GREEN + f'Created CSV file at {output_path}' + RESET)
            else:
                pretty_print_day_stats(
                    params.client, daily_stats, params.minutes_per_day)

    elif params.mode == 'list':
        hourly_wage = params.hourly_wages[client]
        if params.csv:
            output_path = output_work_units_csv(
                work_units, client=params.client, hourly_wage=hourly_wage)
            print(GREEN + f'Created CSV file at {output_path}' + RESET)
        else:
            pretty_print_work_units(
                work_units, client=params.client, hourly_wage=hourly_wage
            )


if __name__ == '__main__':
    app()
