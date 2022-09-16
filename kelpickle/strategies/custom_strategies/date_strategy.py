from __future__ import annotations
from typing import TYPE_CHECKING, TypedDict
from datetime import date

from kelpickle.strategies.custom_strategies.custom_strategy import Strategy

if TYPE_CHECKING:
    from kelpickle.kelpickling import Pickler, Unpickler


class DateReductionResult(TypedDict):
    value: str


class DateStrategy(Strategy):
    @staticmethod
    def reduce(instance: date, pickler: Pickler) -> DateReductionResult:
        return {
            'value': instance.isoformat()
        }

    @staticmethod
    def restore(reduced_object: DateReductionResult, unpickler: Unpickler) -> date:
        return date.fromisoformat(reduced_object['value'])
