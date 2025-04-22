from collections.abc import Generator, Sequence
import datetime as dt

from trackie.ansi_colors import GREEN, RED, RESET
from trackie.conf import Config, get_config
from trackie.work.models import DayStat, WeekStat

from rich.console import Console
from rich.table import Table


class TrackieFormatException(Exception):
    pass


def check_format(lines: Sequence[str], conf: Config | None = None):

    if not conf:
        config = get_config()

    if not config.date_pattern.match(lines[0]):
        raise TrackieFormatException(
            'Format error on Line 1: '
            'First line must be a date.'
        )
    if not config.duration_pattern.match(lines[-1]):
        raise TrackieFormatException(
            'Format error on last Line: '
            'Last line must be a duration.'
        )

    pairs = zip(lines, lines[1:])

    for line_number, pair in enumerate(pairs):
        if config.date_pattern.match(pair[0]):
            if not config.description_pattern.match(pair[1]):
                raise TrackieFormatException(
                    f'Format error on line #{line_number + 1}: '
                    'date is not followed by a description line. '
                    'Hint: description must not start with a number!'
                )
        # elif config.description_pattern.match(pair[0]):
        #     if not config.duration_pattern.match(pair[1]):
        #         raise TrackieFormatException(
        #             f'Format error on line #{line_number + 1}: '
        #             'description not followed by a duration line.'
        #         )
        elif config.duration_pattern.match(pair[0]):
            if not (
                config.date_pattern.match(pair[1])
                or config.description_pattern.match(pair[1])
            ):
                raise TrackieFormatException(
                    f'Format error on line #{line_number + 1}: '
                    'duration is not followed by a description or date line.'
                )
    return True


def daterange(
    start_date: dt.date,
    end_date: dt.date | None = None,
    excluded_weekdays: Sequence[int] | None = None
) -> Generator[dt.date]:
    """
    Generate a sequence of datetime date objects between two dates

    Start_date is inclusive while end_date is not, mimicking range behavior.
    If end_date is omitted the resulting sequence includes today.
    """
    if end_date is None:
        end_date = dt.date.today() + dt.timedelta(days=1)

    days = (end_date - start_date).days
    for n in range(days):
        day = start_date + dt.timedelta(n)
        if excluded_weekdays:
            if day.weekday() in excluded_weekdays:
                continue
        yield day


def daterange_from_week(
    year: int,
    week: int,
    exclude_weekend: bool = False,
) -> tuple[dt.date, dt.date]:
    """
    Computes first and last day of given week

    First day is Monday (1), last is Sunday (0)
    If exclude_weekend is True last_day is Friday (5)
    """
    first_day_of_week = dt.datetime.strptime(f'{year}-{week-1}-1', "%Y-%W-%w").date()  # noqa: E501
    days_delta = 4 if exclude_weekend else 6
    last_day_of_week = first_day_of_week + dt.timedelta(days=days_delta)
    return first_day_of_week, last_day_of_week


def get_week_range(start_date: dt.date, end_date: dt.date) -> Sequence[int]:
    """
    Get (inclusive) week numbers lying between two dates.
    """
    return range(start_date.isocalendar()[1], end_date.isocalendar()[1] + 1)


def pretty_print_day_stats(
    client: str,
    day_stats: Sequence[DayStat],
    minutes_per_day: int
) -> None:
    console = Console()
    table = Table(title=client.capitalize())
    table.add_column("Day")
    table.add_column("#: regular +-")
    table.add_column("Minutes", justify='right')
    table.add_column("Balance", justify='right')
    table.add_column("Carryover", justify='right')
    for day_stat in day_stats:
        parts = []
        hours_per_day = minutes_per_day // 10
        if day_stat.minutes >= minutes_per_day:
            parts.append(f'{(minutes_per_day // 10) * "#"}')
            hours_exceed = (day_stat.minutes - minutes_per_day) // 10
            if hours_exceed:
                parts.append(f'{hours_exceed * "+"}')
        else:
            hours_done = day_stat.minutes // 10
            parts.append(f'{hours_done * "#"}')
            if hours_done < hours_per_day:
                parts.append(f'{(hours_per_day - hours_done) * "-"}')
        balance = day_stat.minutes - minutes_per_day
        table.add_row(
            f'{day_stat.date}',
            ''.join(parts),
            f' {day_stat.minutes} from {minutes_per_day}',
            f'{"+" if balance > 0 else ""}{balance}',
            f'{"+" if day_stat.carryover > 0 else ""}{day_stat.carryover}',
        )
    console.print(table)
    carryover = day_stats[-1].carryover
    print(
        f'Current Balance: {GREEN if carryover >= 0 else RED}'
        f'{"Plus" if carryover > 0 else "Minus"} {carryover}{RESET}'
    )


def pretty_print_week_stats(
    client: str,
    week_stats: Sequence[WeekStat],
    minutes_per_week: int,
) -> None:
    console = Console()
    table = Table(title=client.capitalize())
    table.add_column("Week")
    table.add_column("#: regular +-")
    table.add_column("Minutes", justify='right')
    table.add_column("Balance", justify='right')
    table.add_column("Carryover", justify='right')

    for week_stat in week_stats:
        first_day, last_day = daterange_from_week(
            week_stat.year, week_stat.week, exclude_weekend=True)
        parts = []
        hours_per_week = minutes_per_week // 60
        if week_stat.minutes >= minutes_per_week:
            parts.append(f'{(minutes_per_week // 60) * "#"}')
            hours_exceed = (week_stat.minutes - minutes_per_week) // 60
            if hours_exceed:
                parts.append(f'{hours_exceed * "+"}')
        else:
            hours_done = week_stat.minutes // 60
            parts.append(f'{hours_done * "#"}')
            if hours_done < hours_per_week:
                parts.append(f'{(hours_per_week - hours_done) * "-"}')
        balance = week_stat.minutes - minutes_per_week
        table.add_row(
            f'Nr.{week_stat.week}, {first_day} - {last_day}',
            ''.join(parts),
            f' {week_stat.minutes} from {minutes_per_week}',
            f'{"+" if balance > 0 else ""}{balance}',
            f'{"+" if week_stat.carryover > 0 else ""}{week_stat.carryover}',
        )
    console.print(table)
    carryover = week_stats[-1].carryover
    print(
        f'Current Balance: {GREEN if carryover >= 0 else RED}'
        f'{"Plus" if carryover > 0 else "Minus"} {carryover}{RESET}'
    )
