from dataclasses import dataclass
import os
from pathlib import Path
import tomllib


@dataclass
class Config:
    minutes_per_day: int
    minutes_per_week: int
    vim_otl_filepath: str



def get_config():
    home = Path.home()
    config_file = home / '.trackie.toml'
    with config_file.open('rb') as f:
        cfg = tomllib.load(f)
        env_minutes_per_day = os.environ.get('TRACKIE_MINUTES_PER_DAY')
        if env_minutes_per_day:
            minutes_per_day = int(env_minutes_per_day)
        else:
            minutes_per_day = cfg['minutes_per_day']
        env_minutes_per_week = os.environ.get('TRACKIE_MINUTES_PER_WEEK')
        if env_minutes_per_week:
            minutes_per_week = int(env_minutes_per_week)
        else:
            minutes_per_week = cfg['minutes_per_week']
        config = Config(
            minutes_per_day = minutes_per_day,
            minutes_per_week = minutes_per_week,
            vim_otl_filepath = cfg['vim_otl_filepath'],
        )
    return config

# config = get_config()
