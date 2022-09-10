from __future__ import annotations
from datetime import datetime
from typing import TYPE_CHECKING

from kelpickle.strategies.custom_strategy import ReductionResult

if TYPE_CHECKING:
    from kelpickle.kelpickling import Pickler, Unpickler


class DatetimeStrategyResult(ReductionResult):
    value: str
    fold: int
    tzinfo: ReductionResult


def reduce_datetime(instance: datetime, pickler: Pickler) -> DatetimeStrategyResult:
    return {
        'value': instance.isoformat(),
        'fold': instance.fold,
        'tzinfo': pickler.reduce(instance.tzinfo, relative_key='tzinfo')
    }


def restore_datetime(reduced_object: DatetimeStrategyResult, unpickler: Unpickler) -> datetime:
    restored_tzinfo = unpickler.restore(reduced_object['tzinfo'], relative_key='tzinfo')
    restored_datetime = datetime.fromisoformat(reduced_object['value'])

    return restored_datetime.replace(fold=reduced_object['fold'], tzinfo=restored_tzinfo)
