from collections.abc import Generator, Sequence
import datetime as dt

from .ansi_colors import GREEN, RED, RESET
from .work.models import DayStat, WeekStat

from rich.console import Console
from rich.table import Table
import typer


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
    first_day_of_week = dt.datetime.strptime(f'{year}-{week-1}-1', "%Y-%W-%w").date()
    days_delta = 4 if exclude_weekend else 6
    last_day_of_week = first_day_of_week + dt.timedelta(days=days_delta)
    return first_day_of_week, last_day_of_week


def get_week_range(start_date: dt.date, end_date: dt.date) -> Sequence[int]:
    """
    Get (inclusive) week numbers lying between two dates.
    """
    return range(start_date.isocalendar()[1], end_date.isocalendar()[1] + 1)


def pretty_print_day_stats(day_stats: Sequence[DayStat], minutes_per_day: int) -> None:
    for day_stat in day_stats:
        print(
            f'Date {day_stat.date}: ',
            f'{GREEN}{(day_stat.minutes // 10) * "="}{RESET}',
            f'{day_stat.minutes} from {minutes_per_day}'
        )
    carryover = day_stats[-1].carryover
    print(
        f'Current status: {GREEN if carryover >= 0 else RED}'
        f'{"Plus" if carryover > 0 else "Minus"} {carryover}{RESET}'
    )


def pretty_print_week_stats(
    client: str,
    week_stats: Sequence[WeekStat],
    minutes_per_week: int,
) -> None:
    console = Console()
    table = Table("Week", "Minutes", title=client.capitalize())
    for week_stat in week_stats:
        first_day, last_day = daterange_from_week(
            week_stat.year, week_stat.week, exclude_weekend=True)
        parts = []
        hours_per_week = minutes_per_week // 60
        if week_stat.minutes >= minutes_per_week:
            parts.append(typer.style(
                f'{(minutes_per_week // 60) * "="}',
                fg=typer.colors.WHITE,
            ))
            hours_exceed = (week_stat.minutes - minutes_per_week) // 60
            if hours_exceed:
                parts.append(typer.style(
                    f'{hours_exceed * "="}',
                    fg=typer.colors.GREEN,
                ))
        else:
            hours_done = week_stat.minutes // 60
            parts.append(typer.style(
                f'{hours_done * "="}',
                fg=typer.colors.WHITE,
            ))
            if hours_done < hours_per_week:
                parts.append(typer.style(
                    f'{(hours_per_week - hours_done) * "="}',
                    fg=typer.colors.RED,
                ))
        parts.append(f' {week_stat.minutes} from {minutes_per_week}')
        table.add_row(
            f'Week Number {week_stat.week}, {first_day} - {last_day}',
            ''.join(parts)
        )
    console.print(table)
    carryover = week_stats[-1].carryover
    print(
        f'Current Balance: {GREEN if carryover >= 0 else RED}'
        f'{"Plus" if carryover > 0 else "Minus"} {carryover}{RESET}'
    )
