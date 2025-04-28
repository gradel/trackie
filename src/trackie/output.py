from collections.abc import Generator, Sequence
import csv
import datetime as dt
from decimal import Decimal

from trackie.ansi_colors import GREEN, RED, RESET
from trackie.conf import config
from trackie.utils import daterange_from_week
from trackie.work.models import DayStat, WeekStat, WorkUnit

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


def format_stat_unit(
    stat_unit: DayStat | WeekStat,
    unit_minutes: int,
    balance: int,
    display_hours: bool,
    csv: bool,
):
    if display_hours:
        elapsed = (
            f'{stat_unit.minutes // 60}:{(stat_unit.minutes % 60):02d}'
        )
        if not csv:
            elapsed += f' from {unit_minutes // 60}:{(unit_minutes % 60):02d}'
        balance_str = (
            f'{"+" if balance > 0 else ""}{balance // 60}:'
            f'{(balance % 60):02d}'
        )
        carryover = (
            f'{"+" if stat_unit.carryover > 0 else ""}'
            f'{stat_unit.carryover // 60}:{(stat_unit.carryover % 60):02d}'
        )
    else:
        elapsed = f' {stat_unit.minutes} from {unit_minutes}'
        balance_str = f'{"+" if balance > 0 else ""}{balance}'
        carryover = (
            f'{"+" if stat_unit.carryover > 0 else ""}'
            f'{stat_unit.carryover}'
        )
    return elapsed, balance_str, carryover


def pretty_print_day_stats(
    client: str,
    day_stats: Sequence[DayStat],
    minutes_per_day: int,
    display_hours: bool,
) -> None:
    console = Console()
    table = Table(title=client.capitalize())
    table.add_column("Day")
    table.add_column("#: regular +-")
    table.add_column("Hours" if display_hours else "Minutes", justify='right')
    table.add_column("Balance", justify='right')
    table.add_column("Carryover", justify='right')
    for day_stat in day_stats:
        signs, balance = get_day_balance(day_stat, minutes_per_day)
        elapsed, balance_str, carryover = format_stat_unit(
            day_stat, minutes_per_day, balance, display_hours, csv=False)

        table.add_row(
            f'{day_stat.date}',
            signs,
            elapsed,
            balance_str,
            carryover,
        )
    console.print(table)
    carryover = day_stats[-1].carryover
    if display_hours:
        print(
            f'Current Balance: {GREEN if carryover >= 0 else RED}'
            f'{"Plus" if carryover > 0 else "Minus"} '
            f'{carryover // 60}:{(carryover % 60):02d}{RESET}'
        )
    else:
        print(
            f'Current Balance: {GREEN if carryover >= 0 else RED}'
            f'{"Plus" if carryover > 0 else "Minus"} {carryover}{RESET}'
        )


def output_day_stats_csv(
    client: str,
    day_stats: Sequence[DayStat],
    minutes_per_day: int,
    display_hours: bool,
) -> Path:
    output_path = build_output_path(client, 'daily')

    with open(output_path, 'w', newline='') as csv_file:
        writer = csv.writer(
            csv_file, dialect='excel', quotechar='"', quoting=csv.QUOTE_MINIMAL
        )
        writer.writerow(
            [
                "Day", "Hours" if display_hours else "Minutes", "Balance",
                "Carryover"
            ])
        for day_stat in day_stats:
            signs, balance = get_day_balance(day_stat, minutes_per_day)
            elapsed, balance_str, carryover = format_stat_unit(
                day_stat, minutes_per_day, balance, display_hours, csv=True)

            writer.writerow([
                f'{day_stat.date}',
                elapsed,
                balance_str,
                carryover,
            ])
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
    display_hours: bool,
) -> None:
    console = Console()
    table = Table(title=client.capitalize())
    table.add_column("Week")
    table.add_column("#: regular +-")
    table.add_column(
        "Hours" if display_hours else "Minutes", justify='right')
    table.add_column("Balance", justify='right')
    table.add_column("Carryover", justify='right')

    for week_stat in week_stats:
        first_day, last_day = daterange_from_week(
            week_stat.year, week_stat.week, exclude_weekend=False)

        signs, balance = get_week_balance(week_stat, minutes_per_week)
        elapsed, balance_str, carryover = format_stat_unit(
            week_stat, minutes_per_week, balance, display_hours, csv=False)

        table.add_row(
            f'Nr.{week_stat.week}, {first_day} - {last_day}',
            signs,
            elapsed,
            balance_str,
            carryover,
        )
    console.print(table)
    carryover = week_stats[-1].carryover
    if display_hours:
        print(
            f'Current Balance: {GREEN if carryover >= 0 else RED}'
            f'{"Plus" if carryover > 0 else "Minus"} '
            f'{carryover // 60}:{(carryover % 60):02d}{RESET}'
        )
    else:
        print(
            f'Current Balance: {GREEN if carryover >= 0 else RED}'
            f'{"Plus" if carryover > 0 else "Minus"} {carryover}{RESET}'
        )


def output_week_stats_csv(
    client: str,
    week_stats: Sequence[WeekStat],
    minutes_per_week: int,
    display_hours: bool,
) -> Path:
    output_path = build_output_path(client, 'weekly')

    with open(output_path, 'w', newline='') as csv_file:
        writer = csv.writer(
            csv_file, dialect='excel', quotechar='"', quoting=csv.QUOTE_MINIMAL
        )
        writer.writerow(
            [
                "Week", "Days", "Hours" if display_hours else "Minutes",
                "Balance", "Carryover",
            ])
        for week_stat in week_stats:
            first_day, last_day = daterange_from_week(
                week_stat.year, week_stat.week, exclude_weekend=False)
            signs, balance = get_week_balance(week_stat, minutes_per_week)
            elapsed, balance_str, carryover = format_stat_unit(
                week_stat, minutes_per_week, balance, display_hours, csv=True)

            writer.writerow([
                week_stat.week,
                f'{first_day} - {last_day}',
                elapsed,
                balance_str,
                carryover,
            ])
    return output_path


def pretty_print_work_units(
    work_units,
    *,
    client: str,
    hourly_wage: Decimal,
    display_hours: bool,
) -> None:
    total_cost = Decimal()
    total_minutes = 0
    currency_sign = config.currency_sign or '€'

    console = Console()
    table = Table(title=client.capitalize())
    table.add_column("Work")
    table.add_column(
        f"Duration ({'hours' if display_hours else 'minutes'})",
        justify='right')
    table.add_column(f"Cost ({currency_sign})", justify='right')

    for work_unit in work_units:
        cost = round(Decimal(work_unit.minutes / 60) * hourly_wage, 2)
        total_cost += cost
        total_minutes += work_unit.minutes
        if display_hours:
            duration = (
                f'{work_unit.minutes // 60}:{work_unit.minutes % 60:02d}')
        else:
            duration = str(work_unit.minutes)
        table.add_row(
            work_unit.description,
            duration,
            f"{cost:6.2f}",
        )
    table.add_row('', '', '')
    table.add_row(
        f'Sum ({round(total_minutes / 60, 2)} hours, '
        f'hourly wage: {hourly_wage}{currency_sign})',
        str(total_minutes),
        f"{total_cost:6.2f}",
    )
    console.print(table)


def output_work_units_csv(
    work_units: Generator[WorkUnit],
    *,
    client: str,
    hourly_wage: Decimal,
) -> Path:
    output_path = build_output_path(client, 'list')
    currency_sign = config.currency_sign or '€'

    with open(output_path, 'w', newline='') as csv_file:
        writer = csv.writer(
            csv_file, dialect='excel', quotechar='"', quoting=csv.QUOTE_MINIMAL
        )
        writer.writerow(
            ["Work", "Duration (minutes)", f"Cost ({currency_sign})"])
        for work_unit in work_units:
            cost = round(Decimal(work_unit.minutes / 60) * hourly_wage, 2)
            writer.writerow([
                work_unit.description,
                str(work_unit.minutes),
                str(cost)
            ])
    return output_path
