from trackie.conf import get_config


def test_can_read_work_unit(tmp_path):
    temp_dir = tmp_path / "temp_dir"
    temp_dir.mkdir()

    temp_cfg_file = temp_dir / "cfg.yaml"
    temp_data_file = temp_dir / "data.otl"
    temp_cfg_file.write_text(
        'repository = "file_edit"\n'
        f'[clients]\ntest_client = "{str(temp_data_file)}"'
    )

    config = get_config(temp_cfg_file)

    assert config.repository == 'file_edit'
