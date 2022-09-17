from __future__ import annotations
from datetime import timedelta
from typing import TypedDict

from kelpickle.strategies.custom_strategies.custom_strategy import Strategy, register_strategy
from kelpickle.kelpickling import Pickler, Unpickler


class TimedeltaStrategyResult(TypedDict):
    total_seconds: float


@register_strategy('timedelta', supported_types=timedelta)
class TimeDeltaStrategy(Strategy):
    @staticmethod
    def reduce(instance: timedelta, pickler: Pickler) -> TimedeltaStrategyResult:
        return {
            'total_seconds': instance.total_seconds(),
        }

    @staticmethod
    def restore(reduced_object: TimedeltaStrategyResult, unpickler: Unpickler) -> timedelta:
        return timedelta(seconds=reduced_object['total_seconds'])
