from collections.abc import Generator, Sequence
import csv
import datetime as dt
from decimal import Decimal
from typing import cast

from trackie.ansi_colors import GREEN, RED, RESET
from trackie.conf import Params
from trackie.utils import daterange_from_week
from trackie.work.models import DayStat, WeekStat, WorkUnit

from pathlib import Path
from rich.console import Console
from rich.table import Table


def build_output_path(params: Params) -> Path:
    output_filename = [params.client.lower()]
    output_filename.append(f'-{params.mode}_statistics-')
    output_filename.append(dt.datetime.now().strftime('%Y-%m-%d-%H-%M'))
    output_filename.append('.csv')
    output_path = Path.home() / ''.join(output_filename)
    return output_path


def get_day_balance(
    day_stat: DayStat,
    minutes_per_day: int
) -> tuple[str, int]:
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


def format_hours(value: int) -> str:
    return f'{value // 60}:{(value % 60):02d}'


def format_stat_unit(
    stat_unit: DayStat | WeekStat,
    unit_minutes: int,
    balance: int,
    display_hours: bool,
    csv: bool,
):
    if display_hours:
        elapsed = format_hours(stat_unit.minutes)
        if not csv:
            elapsed += f' from {format_hours(unit_minutes)}'
        balance_str = (
            f'{"+" if balance > 0 else ""}{format_hours(balance)}'
        )
        carryover = (
            f'{"+" if stat_unit.carryover > 0 else ""}'
            + format_hours(stat_unit.carryover)
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
    day_stats: Sequence[DayStat],
    params: Params,
) -> None:
    console = Console()
    table = Table(title=params.client.capitalize())
    table.add_column("Day")
    table.add_column("#: regular +-")
    table.add_column(
        "Hours" if params.display_hours else "Minutes", justify='right')
    table.add_column("Balance", justify='right')
    table.add_column("Carryover", justify='right')

    # checked in evaluate_input
    minutes_per_day = cast(int, params.minutes_per_day)

    for day_stat in day_stats:
        signs, balance = get_day_balance(day_stat, minutes_per_day)
        elapsed, balance_str, carryover = format_stat_unit(
            day_stat, minutes_per_day, balance, params.display_hours,
            csv=False)

        table.add_row(
            f'{day_stat.date}',
            signs,
            elapsed,
            balance_str,
            carryover,
        )
    console.print(table)
    carryover = day_stats[-1].carryover
    if params.display_hours:
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


def output_stats_csv(
    stat_units: Sequence[DayStat] | Sequence[WeekStat],
    params: Params,
) -> Path:
    output_path = build_output_path(params)
    head_row = [
        "Hours" if params.display_hours else "Minutes", "Balance", "Carryover"
    ]
    # already checked in evaluate_input
    minutes_per_day = cast(int, params.minutes_per_day)

    with open(output_path, 'w', newline='') as csv_file:
        writer = csv.writer(
            csv_file, dialect='excel', quotechar='"', quoting=csv.QUOTE_MINIMAL
        )
        if params.interval == 'day':
            stat_units = cast(Sequence[DayStat], stat_units)
            head_row.insert(0, 'Day')
            for day_stat in stat_units:
                signs, balance = get_day_balance(
                    day_stat, minutes_per_day)
                elapsed, balance_str, carryover = format_stat_unit(
                    day_stat, minutes_per_day, balance,
                    params.display_hours, csv=True)

                writer.writerow([
                    f'{day_stat.date}',
                    elapsed,
                    balance_str,
                    carryover,
                ])
        elif params.interval == 'week':
            # already checked in evaluate_input
            minutes_per_week = cast(int, params.minutes_per_week)

            stat_units = cast(Sequence[WeekStat], stat_units)
            head_row = ['Week', 'Days'] + head_row
            writer.writerow(head_row)
            for week_stat in stat_units:
                first_day, last_day = daterange_from_week(
                    week_stat.year, week_stat.week, exclude_weekend=False)
                signs, balance = get_week_balance(
                    week_stat, params.minutes_per_week)
                elapsed, balance_str, carryover = format_stat_unit(
                    week_stat, minutes_per_week, balance,
                    params.display_hours, csv=True)

                writer.writerow([
                    week_stat.week,
                    f'{first_day} - {last_day}',
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
    week_stats: Sequence[WeekStat],
    params: Params,
) -> None:
    console = Console()
    table = Table(title=params.client.capitalize())
    table.add_column("Week")
    table.add_column("#: regular +-")
    table.add_column(
        "Hours" if params.display_hours else "Minutes", justify='right')
    table.add_column("Balance", justify='right')
    table.add_column("Carryover", justify='right')

    # already checked in evaluate_input
    minutes_per_week = cast(int, params.minutes_per_week)

    for week_stat in week_stats:
        first_day, last_day = daterange_from_week(
            week_stat.year, week_stat.week, exclude_weekend=False)

        signs, balance = get_week_balance(week_stat, params.minutes_per_week)
        elapsed, balance_str, carryover = format_stat_unit(
            week_stat, minutes_per_week, balance, params.display_hours,
            csv=False)

        table.add_row(
            f'Nr.{week_stat.week}, {first_day} - {last_day}',
            signs,
            elapsed,
            balance_str,
            carryover,
        )
    console.print(table)
    carryover = week_stats[-1].carryover
    if params.display_hours:
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


def pretty_print_work_units(
    work_units,
    params: Params,
) -> None:
    # checked in evaluate_input
    hourly_wage = cast(Decimal, params.hourly_wage)
    total_cost = Decimal()
    total_minutes = 0

    console = Console()
    table = Table(title=params.client.capitalize())
    table.add_column('Date')
    table.add_column("Work")
    table.add_column(
        f"Duration ({'hours' if params.display_hours else 'minutes'})",
        justify='right')
    table.add_column(f"Cost ({params.currency_sign})", justify='right')

    for work_unit in work_units:
        cost = round(Decimal(work_unit.minutes / 60) * hourly_wage, 2)
        total_cost += cost
        total_minutes += work_unit.minutes
        if params.display_hours:
            duration = format_hours(work_unit.minutes)
        else:
            duration = str(work_unit.minutes)
        table.add_row(
            work_unit.date.strftime('%Y-%m-%d'),
            work_unit.description,
            duration,
            f"{cost:6.2f}",
        )
    table.add_row('', '', '')
    if params.display_hours:
        total_duration = format_hours(total_minutes)
    else:
        total_duration = str(total_minutes)
    table.add_row(
        '',
        f"Sum ({total_duration} "
        f"{'hours' if params.display_hours else 'minutes'}, "
        f'hourly wage: {hourly_wage}{params.currency_sign})',
        total_duration,
        f"{total_cost:6.2f}",
    )
    console.print(table)


def output_work_units_csv(
    work_units: Generator[WorkUnit],
    params,
) -> Path:
    output_path = build_output_path(params)

    with open(output_path, 'w', newline='') as csv_file:
        writer = csv.writer(
            csv_file, dialect='excel', quotechar='"', quoting=csv.QUOTE_MINIMAL
        )
        writer.writerow(
            [
                "Date",
                "Work",
                f"Duration ({'hours' if params.display_hours else 'minutes'})",
                f"Cost ({params.currency_sign})"
            ])
        for work_unit in work_units:
            cost = round(Decimal(
                work_unit.minutes / 60) * params.hourly_wage, 2)
            if params.display_hours:
                duration = format_hours(work_unit.minutes)
            else:
                duration = str(work_unit.minutes)
            writer.writerow([
                work_unit.date.strftime('%Y-%m-%d'),
                work_unit.description,
                duration,
                str(cost)
            ])
    return output_path
