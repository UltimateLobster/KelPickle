from __future__ import annotations
from datetime import time
from typing import TypedDict

from kelpickle.common import Jsonable
from kelpickle.strategies.base_strategy import BaseStrategy, register_strategy
from kelpickle.kelpickling import Pickler, Unpickler


class TimeStrategyResult(TypedDict):
    value: str
    fold: int
    tzinfo: Jsonable


@register_strategy(name='time', supported_types=time, auto_generate_reduction_references=True, consider_subclasses=False)
class TimeStrategy(BaseStrategy):
    def reduce(self, instance: time, pickler: Pickler) -> TimeStrategyResult:
        return {
            'value': instance.isoformat(),
            'fold': instance.fold,
            'tzinfo': pickler.reduce(instance.tzinfo, relative_key='tzinfo')
        }

    def restore_base(self, reduced_instance: TimeStrategyResult, unpickler: Unpickler) -> time:
        restored_tzinfo = unpickler.restore(reduced_instance['tzinfo'], relative_key='tzinfo')
        restored_time = time.fromisoformat(reduced_instance['value'])

        return restored_time.replace(fold=reduced_instance['fold'], tzinfo=restored_tzinfo)
