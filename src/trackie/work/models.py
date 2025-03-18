from dataclasses import dataclass
import datetime as dt


@dataclass
class WorkUnit:
    date: dt.date
    client: str
    minutes: int
    description: str
    start: dt.datetime | None = None
    end: dt.datetime | None = None


@dataclass
class DayStat:
    date: dt.date
    minutes: int
    diff: int
    carryover: int


@dataclass
class WeekStat:
    year: int
    week: int
    minutes: int
    diff: int
    carryover: int
