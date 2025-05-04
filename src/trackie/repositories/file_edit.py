from collections.abc import Generator
import datetime as dt
from pathlib import Path

from trackie.conf import Params
from trackie.utils import (
    check_format,
    error,
    TrackieFormatException,
)
from trackie.repositories.base import WorkRepository
from trackie.work.models import WorkUnit


def get_lines(
    path: Path,
) -> Generator[str]:
    with path.open() as f:
        for line in f:
            if line.strip():
                yield line


class FileEditRepository(WorkRepository):
    @staticmethod
    def get_work_units(params: Params) -> Generator[WorkUnit]:

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

        end_date = params.end_date or dt.date.today()

        # date filter flag
        not_in_range = False
        description = ''

        for line in lines:
            if params.date_pattern.match(line):
                date_str = line.strip()
                date = dt.datetime.strptime(date_str, "%Y-%m-%d").date()
                not_in_range = True if date < params.start_date or date > end_date else False  # noqa: W501
                continue
            elif (
                params.description_pattern.match(line)
                and not_in_range is False
            ):
                description += f' {line.strip()}'
                continue
            elif params.duration_pattern.match(line) and not_in_range is False:
                minutes = int(line.strip())
                work_unit = WorkUnit(date, params.client, minutes, description)
                description = ''
                if work_unit.client.lower() == params.client.lower():
                    yield work_unit

    @staticmethod
    def add_work_unit(work_unit, params: Params) -> None:
        raise NotImplementedError(f'Go and edit {params.data_path} by hand.')
