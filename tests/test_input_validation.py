from trackie.cli import (
    no_default_client_message,
    client_not_found_message,
    file_does_not_exist_message,
    invalid_start_date_format_message,
    evaluate_input,
)
from trackie.conf import Config

import pytest

# clients
#  mode
#  start_date
#  hourly_wages
#  minutes_per_day
#  minutes_per_week
#  abbr
#  spaces
#  default
#  interval


def test_no_config_values_and_no_args_errors():
    config = Config(
        clients=None,
    )
    with pytest.raises(SystemExit) as e:
        evaluate_input(
            client=None,
            mode=None,
            start=None,
            interval=None,
            csv=False,
            config=config,
        )
    assert e.match(no_default_client_message)


def test_config_empty_clients_and_no_args_errors():
    config = Config(
        clients={},
    )
    with pytest.raises(SystemExit) as e:
        evaluate_input(
            client=None,
            mode=None,
            start=None,
            interval=None,
            csv=False,
            config=config,
        )
    assert e.match(no_default_client_message)


def test_invalid_client_arg_errors():
    config = Config(
        clients={'client_1': '/some/path'},
    )
    with pytest.raises(SystemExit) as e:
        evaluate_input(
            client='client_2',
            mode=None,
            start=None,
            interval=None,
            csv=False,
            config=config,
        )
    assert e.match(client_not_found_message.format('client_2'))


def test_invalid_data_path():
    config = Config(
        clients={'client': '/tmp/some/path'},
    )
    with pytest.raises(SystemExit) as e:
        evaluate_input(
            client='client',
            mode=None,
            start=None,
            interval=None,
            csv=False,
            config=config,
        )
    assert e.match(file_does_not_exist_message.format('/tmp/some/path'))


def test_invalid_start_arg(tmp_path):
    config = Config(
        clients={'client': '/tmp/some/path'},
    )
    temp_dir = tmp_path / "temp_dir"
    temp_dir.mkdir()
    temp_data_file = temp_dir / "data.otl"
    temp_data_file.write_text('')

    config = Config(
        clients={'client': temp_data_file},
    )
    start_arg = '01.01.2025'

    with pytest.raises(SystemExit) as e:
        evaluate_input(
            client='client',
            mode=None,
            start=start_arg,
            interval=None,
            csv=False,
            config=config,
        )
    assert e.match(invalid_start_date_format_message.format(start=start_arg))
