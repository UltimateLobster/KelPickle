from __future__ import annotations
from typing import TypedDict
from datetime import date

from kelpickle.strategies.base_strategy import BaseStrategy, register_strategy
from kelpickle.kelpickling import Pickler, Unpickler


class DateReductionResult(TypedDict):
    value: str


@register_strategy(name="date", supported_types=date, auto_generate_reduction_references=True)
class DateStrategy(BaseStrategy):
    def reduce(self, instance: date, pickler: Pickler) -> DateReductionResult:
        return {
            'value': instance.isoformat()
        }

    def restore_base(self, reduced_instance: DateReductionResult, unpickler: Unpickler) -> date:
        return date.fromisoformat(reduced_instance['value'])
