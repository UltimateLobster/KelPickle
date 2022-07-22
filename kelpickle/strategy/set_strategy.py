from __future__ import annotations

from typing import TYPE_CHECKING, Iterable

from kelpickle.common import JsonList
from kelpickle.strategy.base_strategy import BaseNonNativeJsonStrategy, JsonicReductionResult

if TYPE_CHECKING:
    from kelpickle.kelpickling import Pickler, Unpickler


class SetReductionResult(JsonicReductionResult):
    value: JsonList


class SetStrategy(BaseNonNativeJsonStrategy[set, SetReductionResult]):
    @staticmethod
    def get_strategy_name() -> str:
        return 'set'

    @staticmethod
    def get_supported_types() -> Iterable[type]:
        return [set]

    @staticmethod
    def reduce(instance: set, pickler: Pickler) -> SetReductionResult:
        return {'value': [pickler.reduce(member) for member in instance]}

    @staticmethod
    def restore(reduced_object: SetReductionResult, unpickler: Unpickler) -> set:
        return {unpickler.restore(member) for member in reduced_object['value']}
