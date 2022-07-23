from datetime import time
from typing import Iterable

from kelpickle.kelpickling import Pickler, Unpickler
from kelpickle.strategy.base_strategy import ReductionResult, JsonicReductionResult, BaseNonNativeJsonStrategy


class TimeStrategyResult(JsonicReductionResult):
    value: str
    fold: int
    tzinfo: ReductionResult


class TimeStrategy(BaseNonNativeJsonStrategy[time, TimeStrategyResult]):
    @staticmethod
    def get_strategy_name() -> str:
        return 'time'

    @staticmethod
    def get_supported_types() -> Iterable[type]:
        return [time]

    @staticmethod
    def reduce(instance: time, pickler: Pickler) -> TimeStrategyResult:
        return {
            'value': instance.isoformat(),
            'fold': instance.fold,
            'tzinfo': pickler.reduce(instance.tzinfo)
        }

    @staticmethod
    def restore(reduced_object: TimeStrategyResult, unpickler: Unpickler) -> time:
        restored_tzinfo = unpickler.restore(reduced_object['tzinfo'])
        restored_time = time.fromisoformat(reduced_object['value'])

        return restored_time.replace(fold=reduced_object['fold'], tzinfo=restored_tzinfo)
