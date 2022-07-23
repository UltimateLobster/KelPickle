from datetime import timedelta
from typing import Iterable

from kelpickle.kelpickling import Pickler, Unpickler
from kelpickle.strategy.base_strategy import JsonicReductionResult, BaseNonNativeJsonStrategy


class TimedeltaStrategyResult(JsonicReductionResult):
    total_seconds: float


class TimedeltaStrategy(BaseNonNativeJsonStrategy[timedelta, TimedeltaStrategyResult]):
    @staticmethod
    def get_strategy_name() -> str:
        return 'timedelta'

    @staticmethod
    def get_supported_types() -> Iterable[type]:
        return [timedelta]

    @staticmethod
    def reduce(instance: timedelta, pickler: Pickler) -> TimedeltaStrategyResult:
        return {
            'total_seconds': instance.total_seconds(),
        }

    @staticmethod
    def restore(reduced_object: TimedeltaStrategyResult, unpickler: Unpickler) -> timedelta:
        return timedelta(seconds=reduced_object['total_seconds'])
