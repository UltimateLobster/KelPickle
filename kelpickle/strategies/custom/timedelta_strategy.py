from __future__ import annotations
from datetime import timedelta
from typing import TYPE_CHECKING

from kelpickle.strategies.custom_strategy import ReductionResult

if TYPE_CHECKING:
    from kelpickle.kelpickling import Pickler, Unpickler


class TimedeltaStrategyResult(ReductionResult):
    total_seconds: float


def reduce_timedelta(instance: timedelta, pickler: Pickler) -> TimedeltaStrategyResult:
    return {
        'total_seconds': instance.total_seconds(),
    }


def restore_timedelta(reduced_object: TimedeltaStrategyResult, unpickler: Unpickler) -> timedelta:
    return timedelta(seconds=reduced_object['total_seconds'])
