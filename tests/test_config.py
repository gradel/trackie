from trackie.conf import get_config


def test_config_file_with_only_client_sets_default_client_entry(tmp_path):
    temp_dir = tmp_path / "temp_dir"
    temp_dir.mkdir()

    temp_cfg_file = temp_dir / "cfg.yaml"
    temp_data_file = temp_dir / "data.otl"
    temp_cfg_file.write_text(
        f'[clients]\ntest_client = "{str(temp_data_file)}"'
    )

    config = get_config(temp_cfg_file)

    assert config.mode is None
    assert config.clients == {'test_client': str(temp_data_file)}
    assert config.start_date is None
    assert config.hourly_wages is None
    assert config.minutes_per_day is None
    assert config.minutes_per_week is None
    assert config.abbr is None
    assert config.spaces is None
    assert config.default is None
