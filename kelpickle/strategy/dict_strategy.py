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
            # TODO: This is just temporary values for the dictionary relative keys. We would need to reconsider them
            #      in order to maintain readability and when reading the result manually as well as consistency between
            #      pickling and unpickling.
            pickler.reduce(key, relative_key=f"{i}_KEY"): pickler.reduce(value, relative_key=str(i))
            for i, (key, value) in enumerate(instance.items())
        }

    @staticmethod
    def restore(reduced_object: ReductionResult, unpickler: Unpickler) -> dict:
        result = {}
        for i, (key, value) in enumerate(reduced_object.items()):
            result[unpickler.restore(key, relative_key=f"{i}_KEY")] = unpickler.restore(value, relative_key=str(i))

        return result
