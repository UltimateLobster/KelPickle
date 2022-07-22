from __future__ import annotations

from typing import TYPE_CHECKING, Iterable

from kelpickle.strategy.base_strategy import BaseStrategy, ReductionResult

if TYPE_CHECKING:
    from kelpickle.kelpickling import Pickler, Unpickler


class DictStrategy(BaseStrategy[dict, dict]):
    @staticmethod
    def get_strategy_name() -> str:
        return "dict"

    @staticmethod
    def get_supported_types() -> Iterable[type]:
        return [dict]

    @staticmethod
    def reduce(instance: dict, pickler: Pickler) -> ReductionResult:
        return {
            pickler.reduce(key): pickler.reduce(value)
            for key, value in instance.items()
        }

    @staticmethod
    def restore(reduced_object: ReductionResult, unpickler: Unpickler) -> dict:
        result = {}
        for key, value in reduced_object.items():
            result[unpickler.restore(key)] = unpickler.restore(value)

        return result
