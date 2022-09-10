from __future__ import annotations
from typing import TYPE_CHECKING
from datetime import date

from kelpickle.strategies.custom_strategy import ReductionResult

if TYPE_CHECKING:
    from kelpickle.kelpickling import Pickler, Unpickler


class DateReductionResult(ReductionResult):
    value: str


def reduce_date(instance: date, pickler: Pickler) -> DateReductionResult:
    return {
        'value': instance.isoformat()
    }


def restore_date(reduced_object: DateReductionResult, unpickler: Unpickler) -> date:
    return date.fromisoformat(reduced_object['value'])
