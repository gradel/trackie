import datetime as dt

import pytest

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
