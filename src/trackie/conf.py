from dataclasses import dataclass
import datetime as dt
from pathlib import Path
import re
import tomllib

date_pattern = re.compile(r'''
    ^20[23]\d-  # year
    (01|02|03|04|05|06|07|08|09|10|11|12)-     # month
    (01|02|03|04|05|06|07|08|09|10|11|12|13|14|15|16|17|18|19|20|21|22|23|24|25|26|27|28|29|30|31)$   # day  # noqa: W501
''', re.VERBOSE)

vim_otl_description_pattern = re.compile(r'^\t[^\t].*')
vim_otl_duration_pattern = re.compile(r'^\t\t\d+')


@dataclass
class Config:
    minutes_per_day: int
    minutes_per_week: int
    clients: dict[str, str]
    start_date: dt.date | None = None
    abbr: dict[str, str] | None = None
    date_pattern: re.Pattern = date_pattern
    description_pattern: re.Pattern = vim_otl_description_pattern
    duration_pattern: re.Pattern = vim_otl_duration_pattern
    spaces: int | None = None


def get_config(path: str | None = None):
    if path:
        cfg_file = Path(path)
    else:
        home = Path.home()
        cfg_file = home / '.trackie.toml'
    with cfg_file.open('rb') as f:
        cfg = tomllib.load(f)

    minutes_per_day = cfg['minutes_per_day'] if 'minutes_per_day' in cfg else None  # noqa: W501
    minutes_per_week = cfg['minutes_per_week'] if 'minutes_per_week' in cfg else None  # noqa: W501
    start_date = cfg['start_date'] if 'start_date' in cfg else None
    spaces = cfg['spaces'] if 'spaces' in cfg and cfg['spaces'] else None

    config = Config(
        minutes_per_day=minutes_per_day,
        minutes_per_week=minutes_per_week,
        start_date=start_date,
        clients=cfg['clients'],
        abbr=cfg.get('abbr'),
        spaces=spaces,
    )
    if config.spaces:
        spaces_description_pattern = re.compile(
            r'^ {' + f'{config.spaces}' + r'}[^ ].*')
        spaces_duration_pattern = re.compile(
            r'^ {' + f'{config.spaces * 2}' + r'}\d+')
        config.description_pattern = spaces_description_pattern
        config.duration_pattern = spaces_duration_pattern

    return config
