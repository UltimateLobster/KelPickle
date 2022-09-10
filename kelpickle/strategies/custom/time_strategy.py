from __future__ import annotations
from datetime import time
from typing import TYPE_CHECKING

from kelpickle.strategies.custom_strategy import ReductionResult, ReductionResult

if TYPE_CHECKING:
    from kelpickle.kelpickling import Pickler, Unpickler


class TimeStrategyResult(ReductionResult):
    value: str
    fold: int
    tzinfo: ReductionResult


def reduce_time(instance: time, pickler: Pickler) -> TimeStrategyResult:
    return {
        'value': instance.isoformat(),
        'fold': instance.fold,
        'tzinfo': pickler.reduce(instance.tzinfo, relative_key='tzinfo')
    }


def restore_time(reduced_object: TimeStrategyResult, unpickler: Unpickler) -> time:
    restored_tzinfo = unpickler.restore(reduced_object['tzinfo'], relative_key='tzinfo')
    restored_time = time.fromisoformat(reduced_object['value'])

    return restored_time.replace(fold=reduced_object['fold'], tzinfo=restored_tzinfo)