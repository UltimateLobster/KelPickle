from __future__ import annotations
from datetime import timedelta
from typing import TypedDict

from kelpickle.strategies.base_strategy import BaseStrategy, register_strategy
from kelpickle.kelpickling import Pickler, Unpickler


class TimedeltaStrategyResult(TypedDict):
    total_seconds: float


@register_strategy(name='timedelta', supported_types=timedelta, auto_generate_reduction_references=True, consider_subclasses=False)
class TimeDeltaStrategy(BaseStrategy):
    def reduce(self, instance: timedelta, pickler: Pickler) -> TimedeltaStrategyResult:
        return {
            'total_seconds': instance.total_seconds(),
        }

    def restore_base(self, reduced_instance: TimedeltaStrategyResult, unpickler: Unpickler) -> timedelta:
        return timedelta(seconds=reduced_instance['total_seconds'])
