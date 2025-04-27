from dataclasses import dataclass
import datetime as dt
from decimal import Decimal
from pathlib import Path
import tomllib
from typing import Literal


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
        currency_sign=cfg.get('currency_sign', '€')
    )

    return config


config = get_config()
