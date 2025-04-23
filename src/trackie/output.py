from collections.abc import Sequence
import csv
import datetime as dt

from trackie.ansi_colors import GREEN, RED, RESET
from trackie.utils import daterange_from_week
from trackie.work.models import DayStat, WeekStat

from pathlib import Path
from rich.console import Console
from rich.table import Table


def build_output_path(client, mode):
    output_filename = [client.lower()]
    output_filename.append(f'-{mode}_statistics-')
    output_filename.append(dt.datetime.now().strftime('%Y-%m-%d-%H-%M'))
    output_filename.append('.csv')
    output_path = Path.home() / ''.join(output_filename)
    return output_path


def get_day_balance(day_stat, minutes_per_day):
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
    return ''.join(parts), balance


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
        signs, balance = get_day_balance(day_stat, minutes_per_day)
        table.add_row(
            f'{day_stat.date}',
            signs,
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


def output_day_stats_csv(
    client: str,
    day_stats: Sequence[DayStat],
    minutes_per_day: int
) -> Path:
    output_path = build_output_path(client, 'daily')

    with open(output_path, 'w', newline='') as csv_file:
        writer = csv.writer(
            csv_file, dialect='excel', quotechar='"', quoting=csv.QUOTE_MINIMAL
        )
        writer.writerow(
            ["Day", "#: regular +-", "Minutes", "Balance", "Carryover"])
        for day_stat in day_stats:
            signs, balance = get_day_balance(day_stat, minutes_per_day)
            writer.writerow([
                f'{day_stat.date}',
                signs,
                f' {day_stat.minutes} from {minutes_per_day}',
                f'{"+" if balance > 0 else ""}{balance}',
                f'{"+" if day_stat.carryover > 0 else ""}{day_stat.carryover}',
            ])
        # carryover = day_stats[-1].carryover
    return output_path


def get_week_balance(week_stat, minutes_per_week):
    signs = []
    hours_per_week = minutes_per_week // 60
    if week_stat.minutes >= minutes_per_week:
        signs.append(f'{(minutes_per_week // 60) * "#"}')
        hours_exceed = (week_stat.minutes - minutes_per_week) // 60
        if hours_exceed:
            signs.append(f'{hours_exceed * "+"}')
    else:
        hours_done = week_stat.minutes // 60
        signs.append(f'{hours_done * "#"}')
        if hours_done < hours_per_week:
            signs.append(f'{(hours_per_week - hours_done) * "-"}')
    balance = week_stat.minutes - minutes_per_week
    return ''.join(signs), balance


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

        signs, balance = get_week_balance(week_stat, minutes_per_week)

        table.add_row(
            f'Nr.{week_stat.week}, {first_day} - {last_day}',
            signs,
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


def output_week_stats_csv(
    client: str,
    week_stats: Sequence[DayStat],
    minutes_per_week: int
) -> Path:
    output_path = build_output_path(client, 'weekly')

    with open(output_path, 'w', newline='') as csv_file:
        writer = csv.writer(
            csv_file, dialect='excel', quotechar='"', quoting=csv.QUOTE_MINIMAL
        )
        writer.writerow(
            [
                "Week", "Days", "#: regular +-", "Minutes", "Balance",
                "Carryover"
            ])
        for week_stat in week_stats:
            first_day, last_day = daterange_from_week(
                week_stat.year, week_stat.week, exclude_weekend=True)
            signs, balance = get_week_balance(week_stat, minutes_per_week)

            writer.writerow([
                week_stat.week,
                f'{first_day} - {last_day}',
                signs,
                f' {week_stat.minutes} from {minutes_per_week}',
                f'{"+" if balance > 0 else ""}{balance}',
                f'{"+" if week_stat.carryover > 0 else ""}{week_stat.carryover}',  # noqa: W501
            ])
    return output_path
