from datetime import date
from typing import Iterable

from kelpickle.kelpickling import Pickler, Unpickler
from kelpickle.strategy.base_strategy import BaseNonNativeJsonStrategy, JsonicReductionResult


class DateReductionResult(JsonicReductionResult):
    value: str


class DateStrategy(BaseNonNativeJsonStrategy[date, DateReductionResult]):
    @staticmethod
    def get_strategy_name() -> str:
        return 'date'

    @staticmethod
    def get_supported_types() -> Iterable[type]:
        return [date]

    @staticmethod
    def reduce(instance: date, pickler: Pickler) -> DateReductionResult:
        return {
            'value': instance.isoformat()
        }

    @staticmethod
    def restore(reduced_object: DateReductionResult, unpickler: Unpickler) -> date:
        return date.fromisoformat(reduced_object['value'])
