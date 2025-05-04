from collections.abc import Generator
from typing import Protocol

from trackie.conf import Params
from trackie.work.models import WorkUnit


class WorkRepository(Protocol):
    @staticmethod
    def get_work_units(
        params: Params,
    ) -> Generator[WorkUnit]:
        ...

    @staticmethod
    def add_work_unit(
        work_unit: WorkUnit,
        params: Params,
    ) -> None:
        ...
