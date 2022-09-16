from __future__ import annotations
from datetime import time
from typing import TYPE_CHECKING, TypedDict

from kelpickle.common import Jsonable
from kelpickle.strategies.custom_strategies.custom_strategy import Strategy, register_strategy

if TYPE_CHECKING:
    from kelpickle.kelpickling import Pickler, Unpickler


class TimeStrategyResult(TypedDict):
    value: str
    fold: int
    tzinfo: Jsonable


@register_strategy('time', supported_types=time)
class TimeStrategy(Strategy):
    @staticmethod
    def reduce(instance: time, pickler: Pickler) -> TimeStrategyResult:
        return {
            'value': instance.isoformat(),
            'fold': instance.fold,
            'tzinfo': pickler.reduce(instance.tzinfo, relative_key='tzinfo')
        }

    @staticmethod
    def restore(reduced_object: TimeStrategyResult, unpickler: Unpickler) -> time:
        restored_tzinfo = unpickler.restore(reduced_object['tzinfo'], relative_key='tzinfo')
        restored_time = time.fromisoformat(reduced_object['value'])

        return restored_time.replace(fold=reduced_object['fold'], tzinfo=restored_tzinfo)
