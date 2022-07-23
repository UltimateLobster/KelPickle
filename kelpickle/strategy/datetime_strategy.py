from datetime import datetime
from typing import Iterable

from kelpickle.kelpickling import Pickler, Unpickler
from kelpickle.strategy.base_strategy import JsonicReductionResult, ReductionResult, BaseNonNativeJsonStrategy


class DatetimeStrategyResult(JsonicReductionResult):
    value: str
    fold: int
    tzinfo: ReductionResult


class DatetimeStrategy(BaseNonNativeJsonStrategy[datetime, DatetimeStrategyResult]):
    @staticmethod
    def get_strategy_name() -> str:
        return 'datetime'

    @staticmethod
    def get_supported_types() -> Iterable[type]:
        return [datetime]

    @staticmethod
    def reduce(instance: datetime, pickler: Pickler) -> DatetimeStrategyResult:
        return {
            'value': instance.isoformat(),
            'fold': instance.fold,
            'tzinfo': pickler.reduce(instance.tzinfo)
        }

    @staticmethod
    def restore(reduced_object: DatetimeStrategyResult, unpickler: Unpickler) -> datetime:
        restored_tzinfo = unpickler.restore(reduced_object['tzinfo'])
        restored_datetime = datetime.fromisoformat(reduced_object['value'])

        return restored_datetime.replace(fold=reduced_object['fold'], tzinfo=restored_tzinfo)
