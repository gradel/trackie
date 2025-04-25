from collections.abc import Generator, Sequence
import datetime as dt

from trackie.conf import Config


class TrackieFormatException(Exception):
    pass


def check_format(lines: Sequence[str], config: Config):

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
