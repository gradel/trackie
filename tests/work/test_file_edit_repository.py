import datetime as dt
from pathlib import Path

from trackie.conf import (
    Params,
    date_pattern,
    tabs_description_pattern,
    tabs_duration_pattern,
)
from trackie.repositories.file_edit import FileEditRepository


params_defaults = dict(
    mode='list',
    interval='day',
    csv=False,
    date_pattern=date_pattern,
    description_pattern=tabs_description_pattern,
    duration_pattern=tabs_duration_pattern,
    minutes_per_day=1,
    minutes_per_week=1,
    hourly_wage=None,
    display_hours=True,
    currency_sign='€',
)


def create_data_file(tmp_path, data_text):
    tmp_dir = tmp_path / "temp_dir"
    tmp_dir.mkdir()

    tmp_cfg_file = tmp_dir / "cfg.yaml"
    tmp_data_file = tmp_dir / "data.otl"
    tmp_cfg_file.write_text(
        f'[clients]\ntest_client = "{str(tmp_data_file)}"'
    )
    tmp_data_file.write_text(data_text)
    return tmp_cfg_file, tmp_data_file


def test_empty_file(tmp_path):
    tmp_cfg_file, tmp_data_file = create_data_file(
        tmp_path, '')
    params = Params(
        client='test_client',
        data_path=Path(str(tmp_data_file)),
        start_date=dt.date(year=2025, month=3, day=1),
        **params_defaults,
    )

    assert list(FileEditRepository.get_work_units(params)) == []


def test_one_work_unit(tmp_path):
    tmp_cfg_file, tmp_data_file = create_data_file(
        tmp_path, '2025-03-01\n\tTask 1\n\t\t5')
    params = Params(
        client='test_client',
        data_path=Path(str(tmp_data_file)),
        start_date=dt.date(year=2025, month=3, day=1),
        **params_defaults,
    )

    work_units = list(FileEditRepository.get_work_units(params))
    assert len(work_units) == 1
    work_unit = work_units[0]
    assert work_unit.date.year == 2025
    assert work_unit.date.month == 3
    assert work_unit.date.day == 1


def test_exclude_day_before_start_and_day_after_end(tmp_path):
    first_date = dt.date(2025, 3, 1)
    day_after_first_date = first_date + dt.timedelta(days=1)
    last_date = dt.date(2025, 3, 15)
    day_before_last_date = last_date - dt.timedelta(days=1)
    tmp_cfg_file, tmp_data_file = create_data_file(
        tmp_path, (
            f'{first_date.strftime("%Y-%m-%d")}\n\tTask 1\n\t\t5\n'
            '2025-03-05\n\tTask 2\n\t\t10\n'
            '2025-03-10\n\tTask 3\n\t\t20\n'
            f'{last_date.strftime("%Y-%m-%d")}\n\tTask 4\n\t\t30'
        )
    )
    params = Params(
        client='test_client',
        data_path=Path(str(tmp_data_file)),
        start_date=day_after_first_date,
        end_date=day_before_last_date,
        **params_defaults,
    )
    work_units = list(FileEditRepository.get_work_units(params))
    assert len(work_units) == 2
    first_work_unit, second_work_unit = work_units
    assert first_work_unit.date.day == 5
    assert second_work_unit.date.day == 10
