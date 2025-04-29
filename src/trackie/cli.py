import datetime as dt
from decimal import Decimal, InvalidOperation
from pathlib import Path
import re
from typing import cast, Literal
from typing_extensions import Annotated

import typer

from trackie.conf import (
    config,
    Config,
    Params,
    date_pattern,
    tabs_description_pattern,
    tabs_duration_pattern,
    spaces_description_pattern,
    spaces_duration_pattern,
)
from trackie.utils import error
from trackie.work.logic import handle_command

app = typer.Typer()

no_default_client_message = (
    'No default client is set in the config file, '
    'Provide one as argument or set one in the config file'
)
client_not_found_message = (
    'Error: Client "{}" not found in "clients" table '
    'in YAML config file.'
)
file_does_not_exist_message = 'Error: File "{}" does not exist.'
invalid_start_date_format_message = (
    'Format of start date is invalid: {start}. '
    'Must match YYYY-MM-DD'
)


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
    if client is None:
        error(no_default_client_message)
    client = cast(str, client)

    if config.clients and client:
        try:
            data_path = Path(config.clients[client])
        except KeyError:
            error(client_not_found_message.format(client))

    if not data_path.exists():
        error(file_does_not_exist_message.format(data_path))

    mode = mode or config.mode or 'list'

    if start is None:
        start_date = config.start_date
        if start_date is None:
            today = dt.date.today()
            start_date = dt.date(year=today.year, month=today.month, day=1)
    else:
        try:
            start_date = dt.datetime.strptime(start, '%Y-%m-%d').date()
        except ValueError:
            error(invalid_start_date_format_message.format(start=start))

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

    if config.hourly_wages:
        hourly_wage = config.hourly_wages.get(client)

    if hourly_wage:
        try:
            hourly_wage = Decimal(hourly_wage)
        except InvalidOperation:
            error(
                'Please provide a numerical value for hourly wages.'
            )

    if (
        mode == 'list'
        and not hourly_wage
    ):
        error(
            f'Please provide a hourly wage value for "{client}" in '
            ' the config file when using "list" mode'
        )

    client = cast(str, client)  # just for mypy, params.client has type str
    mode = cast(Literal['list', 'aggregate'], mode)
    interval = cast(Literal['day', 'week'], interval)
    start_date = cast(dt.date, start_date)
    display_hours = cast(bool, config.display_hours)

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
        hourly_wage=hourly_wage,
        display_hours=display_hours,
    )
    return params


def get_default_client() -> str | None:
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
    params = evaluate_input(
        client=client,
        mode=mode,
        start=start,
        interval=interval,
        csv=csv,
        config=config,
    )

    handle_command(params)


if __name__ == '__main__':
    app()
