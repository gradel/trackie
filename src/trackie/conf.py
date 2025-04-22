from dataclasses import dataclass
import datetime as dt
import os
from pathlib import Path
import re
import tomllib


@dataclass
class Config:
    minutes_per_day: int
    minutes_per_week: int
    clients: dict[str, str]
    start_date: dt.date | None = None
    abbr: dict[str, str] | None = None
    date_pattern: re.Pattern = re.compile(r'^20[23]\d-[01]\d-[0123]\d$')
    description_pattern: re.Pattern = re.compile(r'^\t[^\t].*')
    duration_pattern: re.Pattern = re.compile(r'^\t\t\d+')


def get_config(path: str | None = None):
    if path:
        cfg_file = Path(path)
    else:
        home = Path.home()
        cfg_file = home / '.trackie.toml'
    with cfg_file.open('rb') as f:
        cfg = tomllib.load(f)

    env_minutes_per_day = os.getenv('TRACKIE_MINUTES_PER_DAY')
    if env_minutes_per_day:
        minutes_per_day = int(env_minutes_per_day)
    else:
        minutes_per_day = cfg['minutes_per_day']

    env_minutes_per_week = os.getenv('TRACKIE_MINUTES_PER_WEEK')
    if env_minutes_per_week:
        minutes_per_week = int(env_minutes_per_week)
    else:
        minutes_per_week = cfg['minutes_per_week']

    env_start_date = os.getenv('TRACKIE_START_DATE')
    if env_start_date:
        start_date = dt.datetime.strptime(env_start_date, '%Y-%m-%d')
    else:
        start_date = cfg['start_date']

    config = Config(
        minutes_per_day=minutes_per_day,
        minutes_per_week=minutes_per_week,
        start_date=start_date,
        clients=cfg['clients'],
        abbr=cfg.get('abbr')
    )
    if cfg['format'] == 'plain':
        config.description_pattern = re.compile(r"^[^\d].*$")
        config.duration_pattern = re.compile(r"^\d{1,3}$")

    return config
