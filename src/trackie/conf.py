from dataclasses import dataclass
import datetime as dt
from decimal import Decimal
from pathlib import Path
import re
import tomllib
from typing import Literal


date_pattern = re.compile(r'''
    ^20[23]\d-  # year
    (01|02|03|04|05|06|07|08|09|10|11|12)-     # month
    (01|02|03|04|05|06|07|08|09|10|11|12|13|14|15|16|17|18|19|20|21|22|23|24|25|26|27|28|29|30|31)$   # day  # noqa: W501
''', re.VERBOSE)

tabs_description_pattern = re.compile(r'^\t[^\t].*')
tabs_duration_pattern = re.compile(r'^\t\t\d+')

spaces_description_pattern = r'^{}[^ ].*'
spaces_duration_pattern = r'^{}\d+'


@dataclass
class Config:
    clients: dict[str, str] | None
    mode: Literal["list", "aggregate"] | None = None
    start_date: dt.date | None = None
    hourly_wages: dict[str, Decimal] | None = None
    minutes_per_day: int | None = None
    minutes_per_week: int | None = None
    abbr: dict[str, str] | None = None
    spaces: int | None = None
    default: dict[str, dict[str, str]] | None = None
    interval: Literal['day', 'week'] = 'week'
    currency_sign: str | None = '€'
    display_hours: bool | None = True


@dataclass
class Params:
    client: str
    data_path: Path
    mode: Literal['list', 'aggregate']
    start_date: dt.date
    interval: Literal['day', 'week']
    csv: bool
    date_pattern: re.Pattern
    description_pattern: re.Pattern
    duration_pattern: re.Pattern
    minutes_per_day: int | None
    minutes_per_week: int | None
    hourly_wage: Decimal | None
    display_hours: bool
    currency_sign: str | None = '€'


def get_config(path: str | None = None):
    if path:
        cfg_file = Path(path)
    else:
        home = Path.home()
        cfg_file = home / '.trackie.toml'
    with cfg_file.open('rb') as f:
        cfg = tomllib.load(f)

    config = Config(
        clients=cfg.get('clients'),
        mode=cfg.get('mode'),
        start_date=cfg.get('start_date'),
        hourly_wages=cfg.get('hourly-wages'),
        minutes_per_day=cfg.get('minutes_per_day'),
        minutes_per_week=cfg.get('minutes_per_week'),
        abbr=cfg.get('abbr'),
        spaces=cfg.get('spaces'),
        default=cfg.get('default'),
        interval=cfg.get('interval', 'week'),
        currency_sign=cfg.get('currency_sign', '€'),
        display_hours=cfg.get('display_hours', True),
    )

    return config


config = get_config()
