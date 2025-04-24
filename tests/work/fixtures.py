import datetime as dt
import pytest

from trackie.conf import Config
from trackie.work.models import WorkUnit


@pytest.fixture
def single_work_unit():
    def work_unit_gen():
        yield WorkUnit(
            date=dt.date(2025, 1, 10),
            client='client',
            minutes=1,
            description='description'
        )
    yield work_unit_gen()


@pytest.fixture
def tab_config():
    config = Config(
        minutes_per_day=96,
        minutes_per_week=480,
        clients={'mittelhof': '~/non-existing/path'},
    )
    return config
