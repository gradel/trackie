from dataclasses import dataclass
import datetime as dt


@dataclass(frozen=True)
class WorkUnit:
    date: dt.date
    client: str
    minutes: int
    description: str
    description_line_number: int | None = None
    start: dt.datetime | None = None
    end: dt.datetime | None = None


@dataclass(frozen=True)
class DayStat:
    date: dt.date
    minutes: int
    diff: int
    carryover: int


@dataclass(frozen=True)
class WeekStat:
    year: int
    week: int
    minutes: int
    diff: int
    carryover: int
