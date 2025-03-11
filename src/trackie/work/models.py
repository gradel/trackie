from dataclasses import dataclass
import datetime as dt


@dataclass
class WorkUnit:
    date: dt.date
    client: str
    minutes: int
    start: dt.datetime | None = None
    end: dt.datetime | None = None
